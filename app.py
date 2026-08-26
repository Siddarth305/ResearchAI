from flask import (
    Flask,
    render_template,
    request,
    jsonify
)

import requests
import feedparser
import re
import time

from pypdf import PdfReader
from io import BytesIO

from ml.model import ResearchRecommender


app = Flask(__name__)


# Maximum PDF upload size
app.config["MAX_CONTENT_LENGTH"] = (
    10 * 1024 * 1024
)


# Load ML model once
recommender = ResearchRecommender()


ARXIV_API = (
    "https://export.arxiv.org/api/query"
)


SEMANTIC_SCHOLAR_API = (
    "https://api.semanticscholar.org/graph/v1/paper/search"
)


OPENALEX_API = (
    "https://api.openalex.org/works"
)


def get_arxiv_papers(
    query,
    max_results=30,
    attempts=2,
    timeout=(5, 12)
):

    """
    Search arXiv and return paper metadata.
    """

    query = query.strip()


    if not query:

        return []


    search_query = (
        f'all:"{query}"'
    )


    params = {

        "search_query":
            search_query,

        "start":
            0,

        "max_results":
            max_results,

        "sortBy":
            "relevance",

        "sortOrder":
            "descending"

    }


    for attempt in range(attempts):

        try:

            response = requests.get(

                ARXIV_API,

                params=params,

                headers={
                    "User-Agent":
                        "ResearchAI/1.0 (research discovery app)"
                },

                timeout=timeout

            )

            response.raise_for_status()

            break

        except requests.HTTPError as error:

            if (
                error.response is None
                or error.response.status_code != 429
            ):

                raise

            if attempt == attempts - 1:

                raise RuntimeError(
                    "arXiv is temporarily rate-limiting searches. "
                    "Please wait a minute and try again."
                ) from error

            retry_after = error.response.headers.get(
                "Retry-After"
            )

            try:

                delay = min(float(retry_after), 3)

            except (TypeError, ValueError):

                delay = 2 ** attempt

            time.sleep(delay)


    feed = feedparser.parse(

        response.content

    )


    papers = []


    for entry in feed.entries:

        authors = [

            author.name

            for author in entry.get(
                "authors",
                []
            )

        ]


        pdf_url = None


        for link in entry.get(
            "links",
            []
        ):

            if link.get(
                "type"
            ) == "application/pdf":

                pdf_url = link.get(
                    "href"
                )

                break


        papers.append({

            "id":
                entry.get(
                    "id"
                ),

            "title":
                entry.get(
                    "title",
                    ""
                ).strip(),

            "abstract":
                entry.get(
                    "summary",
                    ""
                ).strip(),

            "authors":
                authors,

            "published":
                entry.get(
                    "published",
                    ""
                ),

            "updated":
                entry.get(
                    "updated",
                    ""
                ),

            "categories": [

                category.get(
                    "term"
                )

                for category in entry.get(
                    "tags",
                    []
                )

            ],

            "paper_url":
                entry.get(
                    "link"
                ),

            "pdf_url":
                pdf_url

        })


    return papers


def get_semantic_scholar_papers(
    query,
    max_results=10
):

    response = requests.get(

        SEMANTIC_SCHOLAR_API,

        params={
            "query": query,
            "limit": max_results,
            "fields": (
                "title,abstract,authors,publicationDate,"
                "externalIds,url,openAccessPdf,fieldsOfStudy"
            )
        },

        headers={
            "User-Agent":
                "ResearchAI/1.0 (research discovery app)"
        },

        timeout=(3, 8)

    )

    response.raise_for_status()

    papers = []

    for entry in response.json().get("data", []):

        external_ids = entry.get("externalIds") or {}
        arxiv_id = external_ids.get("ArXiv")
        paper_url = entry.get("url")

        if arxiv_id:
            paper_url = f"https://arxiv.org/abs/{arxiv_id}"

        open_access_pdf = entry.get("openAccessPdf") or {}

        papers.append({

            "id": entry.get("paperId"),
            "title": (entry.get("title") or "").strip(),
            "abstract": (entry.get("abstract") or "").strip(),
            "authors": [
                author.get("name", "")
                for author in entry.get("authors", [])
            ],
            "published": entry.get("publicationDate") or "",
            "updated": "",
            "categories": entry.get("fieldsOfStudy") or [],
            "paper_url": paper_url,
            "pdf_url": open_access_pdf.get("url")

        })

    return papers


def get_openalex_papers(
    query,
    max_results=10
):

    response = requests.get(

        OPENALEX_API,

        params={
            "search": query,
            "per-page": max_results,
            "select": (
                "id,title,publication_date,authorships,"
                "abstract_inverted_index,primary_location,"
                "best_oa_location,concepts"
            )
        },

        headers={
            "User-Agent":
                "ResearchAI/1.0 (research discovery app)"
        },

        timeout=(3, 8)

    )

    response.raise_for_status()

    papers = []

    for entry in response.json().get("results", []):

        abstract_index = entry.get(
            "abstract_inverted_index"
        ) or {}

        abstract_words = [
            (position, word)
            for word, positions in abstract_index.items()
            for position in positions
        ]

        abstract = " ".join(
            word
            for position, word in sorted(abstract_words)
        )

        primary_location = entry.get(
            "primary_location"
        ) or {}

        best_oa_location = entry.get(
            "best_oa_location"
        ) or {}

        papers.append({

            "id": entry.get("id"),
            "title": (entry.get("title") or "").strip(),
            "abstract": abstract,
            "authors": [
                (author.get("author") or {}).get("display_name", "")
                for author in entry.get("authorships", [])
            ],
            "published": entry.get("publication_date") or "",
            "updated": "",
            "categories": [
                concept.get("display_name", "")
                for concept in entry.get("concepts", [])[:5]
            ],
            "paper_url": (
                primary_location.get("landing_page_url")
                or entry.get("id")
            ),
            "pdf_url": best_oa_location.get("pdf_url")

        })

    return papers


def extract_pdf_text(
    pdf_file
):

    """
    Extract text from uploaded PDF.
    """

    pdf_data = pdf_file.read()


    reader = PdfReader(

        BytesIO(
            pdf_data
        )

    )


    extracted_text = ""


    for page in reader.pages:

        text = page.extract_text()


        if text:

            extracted_text += (

                text + "\n"

            )


    return extracted_text


def create_arxiv_query(
    document_text
):

    """
    Create a short arXiv query
    from an uploaded paper.
    """

    text = document_text[:8000]


    text = re.sub(

        r"[^a-zA-Z0-9\s-]",

        " ",

        text

    )


    words = text.split()


    stop_words = {

        "the",
        "and",
        "for",
        "with",
        "this",
        "that",
        "from",
        "using",
        "into",
        "are",
        "was",
        "were",
        "have",
        "has",
        "been",
        "which",
        "their",
        "our",
        "we",
        "they",
        "can",
        "may",
        "more",
        "than",
        "also",
        "such",
        "these",
        "those",
        "not",
        "but",
        "paper",
        "study",
        "method",
        "results",
        "proposed",
        "approach",
        "based",
        "used",
        "use",
        "data"

    }


    useful_words = []


    for word in words:

        word_lower = (
            word.lower()
        )


        if (

            len(word_lower) >= 4

            and
            word_lower not in stop_words

            and
            word_lower not in useful_words

        ):

            useful_words.append(
                word_lower
            )


        if len(
            useful_words
        ) >= 8:

            break


    if not useful_words:

        return "machine learning"


    return " ".join(
        useful_words
    )


@app.route("/")
def home():

    return render_template(
        "index.html"
    )


@app.route(
    "/api/search"
)
def search_papers():

    query = request.args.get(
        "query",
        ""
    ).strip()


    sort_by = request.args.get(

        "sort",

        "relevance"

    )


    category = request.args.get(

        "category",

        "all"

    )


    if not query:

        return jsonify({

            "success":
                False,

            "message":
                "Please enter a research topic."

        }), 400


    try:

        papers = get_arxiv_papers(

            query,

            30

        )


        # ML semantic ranking

        papers = recommender.rank_papers(

            query,

            papers

        )


        # Category filtering

        if category != "all":

            papers = [

                paper

                for paper in papers

                if category in
                paper.get(
                    "categories",
                    []
                )

            ]


        # Sorting

        if sort_by == "newest":

            papers.sort(

                key=lambda x:
                    x.get(
                        "published",
                        ""
                    ),

                reverse=True

            )


        elif sort_by == "oldest":

            papers.sort(

                key=lambda x:
                    x.get(
                        "published",
                        ""
                    )

            )


        else:

            papers.sort(

                key=lambda x:
                    x.get(
                        "similarity_score",
                        0
                    ),

                reverse=True

            )


        # --------------------------------
        # CLUSTERING
        # --------------------------------

        clusters = (
            recommender.cluster_papers(
                papers,
                4
            )
        )


        # Top 10 papers

        top_papers = papers[:10]


        return jsonify({

            "success":
                True,

            "query":
                query,

            "candidate_papers":
                len(papers),

            "papers":
                top_papers,

            "clusters":
                clusters

        })


    except Exception as e:

        return jsonify({

            "success":
                False,

            "message":
                f"Search failed: {str(e)}"

        }), 500


@app.route(
    "/api/upload",
    methods=["POST"]
)
def upload_paper():

    """
    Upload a research paper
    and find similar papers.
    """

    if "file" not in request.files:

        return jsonify({

            "success":
                False,

            "message":
                "No PDF file uploaded."

        }), 400


    file = request.files["file"]


    if file.filename == "":

        return jsonify({

            "success":
                False,

            "message":
                "Please select a PDF file."

        }), 400


    if not file.filename.lower().endswith(
        ".pdf"
    ):

        return jsonify({

            "success":
                False,

            "message":
                "Only PDF files are allowed."

        }), 400


    try:

        extracted_text = (
            extract_pdf_text(
                file
            )
        )


        extracted_text = (
            extracted_text.strip()
        )


        if len(
            extracted_text
        ) < 100:

            return jsonify({

                "success":
                    False,

                "message":
                    "Could not extract enough text from this PDF."

            }), 400


        arxiv_query = (
            create_arxiv_query(
                extracted_text
            )
        )


        print(
            f"PDF search query: {arxiv_query}"
        )


        try:

            papers = get_arxiv_papers(

                arxiv_query,

                10,
                attempts=1,
                timeout=(3, 7)

            )

        except Exception as error:

            print(
                "ARXIV PDF SEARCH ERROR:",
                str(error)
            )

            try:

                papers = get_semantic_scholar_papers(

                    arxiv_query,

                    10

                )

            except Exception as fallback_error:

                print(
                    "SEMANTIC SCHOLAR PDF SEARCH ERROR:",
                    str(fallback_error)
                )

                try:

                    papers = get_openalex_papers(

                        arxiv_query,

                        10

                    )

                except Exception as openalex_error:

                    print(
                        "OPENALEX PDF SEARCH ERROR:",
                        str(openalex_error)
                    )

                    papers = []


        if not papers:

            try:

                papers = get_semantic_scholar_papers(

                    arxiv_query,

                    10

                )

            except Exception:

                try:

                    papers = get_openalex_papers(

                        arxiv_query,

                        10

                    )

                except Exception as openalex_error:

                    print(
                        "OPENALEX PDF SEARCH ERROR:",
                        str(openalex_error)
                    )

                    papers = []


        if papers:

            papers = (
                recommender
                .rank_papers_by_document(
                    extracted_text,
                    papers
                )
            )


        # Cluster similar papers

        clusters = (
            recommender.cluster_papers(
                papers,
                4
            )
        )


        top_papers = papers[:10]


        return jsonify({

            "success":
                True,

            "filename":
                file.filename,

            "text_length":
                len(
                    extracted_text
                ),

            "search_query":
                arxiv_query,

            "candidate_papers":
                len(
                    papers
                ),

            "search_warning":
                "Similar papers are temporarily unavailable because "
                "arXiv is rate-limiting requests."
                if not papers
                else "",

            "papers":
                top_papers,

            "clusters":
                clusters

        })


    except Exception as e:

        print(
            "PDF ERROR:",
            str(e)
        )


        return jsonify({

            "success":
                False,

            "message":
                f"PDF processing failed: {str(e)}"

        }), 500


@app.errorhandler(
    413
)
def file_too_large(error):

    return jsonify({

        "success":
            False,

        "message":
            "PDF is too large. Maximum size is 10 MB."

    }), 413


if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True

    )