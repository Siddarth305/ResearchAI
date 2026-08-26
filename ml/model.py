from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import numpy as np


class ResearchRecommender:

    def __init__(self):

        print("Loading ML model...")

        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

        print("ML model loaded.")


    def create_embedding(self, text):

        """
        Convert text into a semantic vector.
        """

        embedding = self.model.encode(
            [text],
            convert_to_numpy=True
        )

        return embedding


    def create_embeddings(self, texts):

        """
        Convert multiple texts into semantic vectors.
        """

        return self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False
        )


    def rank_papers(self, query, papers):

        """
        Rank papers based on semantic similarity
        to the user's search query.
        """

        if not papers:

            return []


        query_embedding = self.create_embedding(
            query
        )


        paper_texts = []


        for paper in papers:

            title = paper.get(
                "title",
                ""
            )

            abstract = paper.get(
                "abstract",
                ""
            )


            combined_text = (
                f"{title}. {abstract}"
            )


            paper_texts.append(
                combined_text
            )


        paper_embeddings = self.create_embeddings(
            paper_texts
        )


        similarities = cosine_similarity(

            query_embedding,

            paper_embeddings

        )[0]


        for paper, similarity in zip(
            papers,
            similarities
        ):

            paper["similarity_score"] = round(

                float(similarity) * 100,

                2

            )


        papers.sort(

            key=lambda x:
                x.get(
                    "similarity_score",
                    0
                ),

            reverse=True

        )


        return papers


    def rank_papers_by_document(
        self,
        document_text,
        papers
    ):

        """
        Rank papers based on similarity
        to an uploaded research paper.
        """

        if not papers:

            return []


        document_embedding = self.create_embedding(

            document_text

        )


        paper_texts = []


        for paper in papers:

            title = paper.get(
                "title",
                ""
            )

            abstract = paper.get(
                "abstract",
                ""
            )


            combined_text = (
                f"{title}. {abstract}"
            )


            paper_texts.append(
                combined_text
            )


        paper_embeddings = self.create_embeddings(

            paper_texts

        )


        similarities = cosine_similarity(

            document_embedding,

            paper_embeddings

        )[0]


        for paper, similarity in zip(

            papers,

            similarities

        ):

            paper["similarity_score"] = round(

                float(similarity) * 100,

                2

            )


        papers.sort(

            key=lambda x:
                x.get(
                    "similarity_score",
                    0
                ),

            reverse=True

        )


        return papers


    def cluster_papers(
        self,
        papers,
        number_of_clusters=4
    ):

        """
        Group papers into semantic research topics
        using K-Means clustering.
        """

        if not papers:

            return []


        # We need at least two papers
        if len(papers) < 2:

            return []


        paper_texts = []


        for paper in papers:

            title = paper.get(
                "title",
                ""
            )

            abstract = paper.get(
                "abstract",
                ""
            )


            paper_texts.append(

                f"{title}. {abstract}"

            )


        embeddings = self.create_embeddings(

            paper_texts

        )


        # Never create more clusters than papers

        number_of_clusters = min(

            number_of_clusters,

            len(papers)

        )


        kmeans = KMeans(

            n_clusters=number_of_clusters,

            random_state=42,

            n_init=10

        )


        labels = kmeans.fit_predict(
            embeddings
        )


        # Add cluster information to papers

        for paper, label in zip(
            papers,
            labels
        ):

            paper["cluster"] = int(
                label
            )


        clusters = []


        for cluster_id in range(
            number_of_clusters
        ):

            cluster_papers = [

                paper

                for paper in papers

                if paper["cluster"]
                == cluster_id

            ]


            if not cluster_papers:

                continue


            # Calculate cluster size

            cluster_size = len(
                cluster_papers
            )


            # Find representative paper
            # closest to the cluster center

            cluster_indices = [

                index

                for index, paper in enumerate(
                    papers
                )

                if paper["cluster"]
                == cluster_id

            ]


            center = kmeans.cluster_centers_[

                cluster_id

            ]


            cluster_embeddings = embeddings[
                cluster_indices
            ]


            distances = np.linalg.norm(

                cluster_embeddings - center,

                axis=1

            )


            representative_index = (

                cluster_indices[
                    int(
                        np.argmin(
                            distances
                        )
                    )
                ]

            )


            representative_paper = papers[
                representative_index
            ]


            # Use representative paper title
            # as the initial cluster name

            cluster_name = (
                representative_paper
                .get(
                    "title",
                    f"Research Group {cluster_id + 1}"
                )
            )


            clusters.append({

                "id": cluster_id,

                "name": cluster_name,

                "size": cluster_size,

                "papers": cluster_papers

            })


        # Largest groups first

        clusters.sort(

            key=lambda x:
                x["size"],

            reverse=True

        )


        return clusters