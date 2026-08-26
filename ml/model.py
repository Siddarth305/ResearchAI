from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import numpy as np
import re


class ResearchRecommender:

    def __init__(self):
        pass

    # ==================================================
    # CLEAN TEXT
    # ==================================================

    def _clean_text(self, text):

        if not text:
            return ""

        text = str(text).lower()

        text = re.sub(
            r"[^a-z0-9\s-]",
            " ",
            text
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()


    # ==================================================
    # PAPER TEXT
    # ==================================================

    def _paper_text(self, paper):

        title = paper.get(
            "title",
            ""
        )

        abstract = paper.get(
            "abstract",
            ""
        )

        categories = " ".join(
            paper.get(
                "categories",
                []
            )
        )

        # Give title more importance
        return (
            f"{title} {title} {title} "
            f"{abstract} "
            f"{categories}"
        )


    # ==================================================
    # KEYWORD EXTRACTION
    # ==================================================

    def _keywords(self, text):

        text = self._clean_text(text)

        words = text.split()

        stop_words = {
            "this",
            "that",
            "with",
            "from",
            "using",
            "used",
            "into",
            "their",
            "there",
            "these",
            "those",
            "which",
            "where",
            "when",
            "what",
            "will",
            "would",
            "could",
            "should",
            "have",
            "has",
            "been",
            "were",
            "was",
            "are",
            "and",
            "the",
            "for",
            "not",
            "but",
            "also",
            "than",
            "then",
            "such",
            "based",
            "paper",
            "study",
            "method",
            "methods",
            "results",
            "approach",
            "proposed",
            "data"
        }

        keywords = []

        for word in words:

            if (
                len(word) >= 4
                and word not in stop_words
                and word not in keywords
            ):

                keywords.append(word)

        return keywords


    # ==================================================
    # KEYWORD OVERLAP
    # ==================================================

    def _keyword_similarity(
        self,
        document_text,
        paper
    ):

        document_words = set(
            self._keywords(
                document_text
            )
        )

        paper_text = self._paper_text(
            paper
        )

        paper_words = set(
            self._keywords(
                paper_text
            )
        )

        if not document_words:
            return 0.0

        if not paper_words:
            return 0.0

        common_words = (
            document_words &
            paper_words
        )

        return (
            len(common_words) /
            len(document_words)
        )


    # ==================================================
    # RANK SEARCH PAPERS
    # ==================================================

    def rank_papers(
        self,
        query,
        papers
    ):

        if not papers:
            return []

        query = self._clean_text(
            query
        )

        documents = [
            self._paper_text(paper)
            for paper in papers
        ]

        try:

            # WORD TF-IDF

            word_vectorizer = TfidfVectorizer(
                stop_words="english",
                max_features=6000,
                ngram_range=(1, 2),
                sublinear_tf=True
            )

            all_text = [
                query
            ] + documents

            word_vectors = (
                word_vectorizer
                .fit_transform(
                    all_text
                )
            )

            word_scores = cosine_similarity(
                word_vectors[0:1],
                word_vectors[1:]
            )[0]


            # CHARACTER TF-IDF

            char_vectorizer = TfidfVectorizer(
                analyzer="char_wb",
                ngram_range=(3, 5),
                max_features=8000,
                sublinear_tf=True
            )

            char_vectors = (
                char_vectorizer
                .fit_transform(
                    all_text
                )
            )

            char_scores = cosine_similarity(
                char_vectors[0:1],
                char_vectors[1:]
            )[0]


        except Exception as error:

            print(
                "SEARCH TF-IDF ERROR:",
                error
            )

            word_scores = np.zeros(
                len(papers)
            )

            char_scores = np.zeros(
                len(papers)
            )


        for index, paper in enumerate(
            papers
        ):

            word_score = float(
                word_scores[index]
            )

            char_score = float(
                char_scores[index]
            )

            # Combine both scores

            final_score = (
                word_score * 0.75
                +
                char_score * 0.25
            )

            paper[
                "similarity_score"
            ] = round(
                min(
                    final_score * 100,
                    100
                ),
                2
            )


        papers.sort(
            key=lambda paper:
                paper.get(
                    "similarity_score",
                    0
                ),
            reverse=True
        )

        return papers


    # ==================================================
    # RANK PAPERS AGAINST PDF
    # ==================================================

    def rank_papers_by_document(
        self,
        document_text,
        papers
    ):

        if not papers:
            return []

        document_text = (
            self._clean_text(
                document_text
            )
        )

        documents = [
            self._paper_text(paper)
            for paper in papers
        ]

        try:

            # ------------------------------------------
            # WORD TF-IDF
            # ------------------------------------------

            word_vectorizer = TfidfVectorizer(
                stop_words="english",
                max_features=10000,
                ngram_range=(1, 2),
                sublinear_tf=True
            )

            all_text = [
                document_text
            ] + documents

            word_vectors = (
                word_vectorizer
                .fit_transform(
                    all_text
                )
            )

            word_scores = cosine_similarity(
                word_vectors[0:1],
                word_vectors[1:]
            )[0]


            # ------------------------------------------
            # CHARACTER TF-IDF
            # ------------------------------------------

            char_vectorizer = TfidfVectorizer(
                analyzer="char_wb",
                ngram_range=(3, 5),
                max_features=12000,
                sublinear_tf=True
            )

            char_vectors = (
                char_vectorizer
                .fit_transform(
                    all_text
                )
            )

            char_scores = cosine_similarity(
                char_vectors[0:1],
                char_vectors[1:]
            )[0]


        except Exception as error:

            print(
                "PDF TF-IDF ERROR:",
                error
            )

            word_scores = np.zeros(
                len(papers)
            )

            char_scores = np.zeros(
                len(papers)
            )


        for index, paper in enumerate(
            papers
        ):

            word_score = float(
                word_scores[index]
            )

            char_score = float(
                char_scores[index]
            )


            # ------------------------------------------
            # KEYWORD OVERLAP
            # ------------------------------------------

            keyword_score = (
                self._keyword_similarity(
                    document_text,
                    paper
                )
            )


            # ------------------------------------------
            # HYBRID SCORE
            # ------------------------------------------

            final_score = (

                word_score * 0.60

                +

                char_score * 0.20

                +

                keyword_score * 0.20

            )


            # Prevent tiny values from
            # displaying as 0

            if (
                final_score > 0
                and final_score < 0.01
            ):

                final_score = 0.01


            paper[
                "similarity_score"
            ] = round(
                min(
                    final_score * 100,
                    100
                ),
                2
            )


        papers.sort(
            key=lambda paper:
                paper.get(
                    "similarity_score",
                    0
                ),
            reverse=True
        )


        return papers


    # ==================================================
    # CLUSTER PAPERS
    # ==================================================

    def cluster_papers(
        self,
        papers,
        n_clusters=4
    ):

        if not papers:
            return []


        if len(papers) < 2:

            return [
                {
                    "name": "Research",
                    "size": len(papers)
                }
            ]


        documents = [
            self._paper_text(paper)
            for paper in papers
        ]


        try:

            vectorizer = TfidfVectorizer(
                stop_words="english",
                max_features=3000,
                ngram_range=(1, 2),
                sublinear_tf=True
            )


            vectors = (
                vectorizer
                .fit_transform(
                    documents
                )
            )


            actual_clusters = min(
                n_clusters,
                len(papers)
            )


            if actual_clusters < 2:

                return [
                    {
                        "name": "Research",
                        "size": len(papers)
                    }
                ]


            model = KMeans(
                n_clusters=actual_clusters,
                random_state=42,
                n_init=10
            )


            labels = model.fit_predict(
                vectors
            )


            feature_names = (
                vectorizer
                .get_feature_names_out()
            )


            clusters = []


            for cluster_id in range(
                actual_clusters
            ):

                indexes = [
                    i
                    for i, label
                    in enumerate(labels)
                    if label == cluster_id
                ]


                if not indexes:
                    continue


                center = (
                    model
                    .cluster_centers_[
                        cluster_id
                    ]
                )


                top_indices = (
                    center.argsort()[
                        ::-1
                    ][:5]
                )


                keywords = [
                    feature_names[index]
                    for index in top_indices
                ]


                if keywords:

                    name = " · ".join(
                        keywords[:3]
                    )

                else:

                    name = (
                        f"Research Cluster "
                        f"{cluster_id + 1}"
                    )


                clusters.append(
                    {
                        "name": name,
                        "size": len(indexes)
                    }
                )


            clusters.sort(
                key=lambda cluster:
                    cluster["size"],
                reverse=True
            )


            return clusters


        except Exception as error:

            print(
                "CLUSTERING ERROR:",
                error
            )


            return [
                {
                    "name": "Research",
                    "size": len(papers)
                }
            ]   