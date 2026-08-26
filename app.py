from flask import (
    Flask,
    render_template,
    request,
    jsonify
)

import requests
import feedparser
import re

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


def get_arxiv_papers(
    query,
    max_results=30
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


    response = requests.get(

        ARXIV_API,

        params=params,

        timeout=30

    )


    response.raise_for_status()


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


        papers = get_arxiv_papers(

            arxiv_query,

            30

        )


        if not papers:

            papers = get_arxiv_papers(

                "machine learning",

                30

            )


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