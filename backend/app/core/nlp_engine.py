import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import AgglomerativeClustering


class SemanticClusterEngine:
    """
    NLP Engine for GhostGrid:
    1. Generates 384-dimensional dense vectors using 'all-MiniLM-L6-v2'.
    2. Clusters semantically equivalent claims (Agglomerative Clustering).
    3. Isolates singleton organic noise from coordinated multi-post narratives.
    4. Computes cluster centroids and selects canonical representative claims.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        print(f"[NLP Engine] Loading embedding model '{model_name}' onto CPU...")
        self.model = SentenceTransformer(model_name)
        print("[NLP Engine] Model loaded successfully.")

    def compute_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Encodes list of strings into normalized 384-dim dense float embeddings.
        Normalizing guarantees dot product equals cosine similarity.
        """
        if not texts:
            return np.empty((0, 384), dtype=np.float32)
        return self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

    def cluster_posts(
        self,
        posts: List[Dict[str, Any]],
        similarity_threshold: float = 0.80,
        min_cluster_size: int = 2
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
        """
        Clusters posts based on semantic similarity.
        
        Args:
            posts: List of post dicts with at least 'post_id' and 'text'.
            similarity_threshold: Cosine similarity cutoff (e.g. 0.80 means 80% semantic match).
            min_cluster_size: Minimum posts required to constitute an actual Narrative (default: 2).
                              Posts below this are treated as uncoordinated singletons (organic).
        
        Returns:
            annotated_posts: Input posts enriched with 'narrative_id' and 'centroid_similarity'.
            narratives: Dict mapping narrative_id to metadata (canonical claim, post count, etc.).
        """
        if not posts:
            return [], {}

        texts = [p["text"] for p in posts]
        embeddings = self.compute_embeddings(texts)

        n_samples = len(posts)
        if n_samples < min_cluster_size:
            # Not enough posts to form any cluster
            annotated = [
                {**p, "narrative_id": None, "centroid_similarity": 1.0, "is_narrative": False}
                for p in posts
            ]
            return annotated, {}

        # 1. Compute cosine distance matrix (Distance = 1.0 - Similarity)
        # Bounded between 0.0 and 2.0 to avoid any floating-point roundoff errors
        sim_matrix = cosine_similarity(embeddings)
        dist_matrix = np.clip(1.0 - sim_matrix, 0.0, 2.0)

        # 2. Run Agglomerative Clustering with distance threshold
        # distance_threshold = 1.0 - similarity_threshold (e.g. 1.0 - 0.80 = 0.20)
        max_distance = max(0.01, 1.0 - similarity_threshold)
        clustering = AgglomerativeClustering(
            metric="precomputed",
            linkage="average",
            distance_threshold=max_distance,
            n_clusters=None
        )
        raw_labels = clustering.fit_predict(dist_matrix)

        # 3. Analyze cluster counts and filter out singletons (noise / organic one-offs)
        unique_labels, counts = np.unique(raw_labels, return_counts=True)
        label_to_count = dict(zip(unique_labels, counts))

        # Assign canonical narrative IDs only to clusters with size >= min_cluster_size
        narrative_counter = 1
        raw_to_narrative_id = {}
        for label, count in label_to_count.items():
            if count >= min_cluster_size:
                narrative_id = f"narrative_{narrative_counter:02d}"
                raw_to_narrative_id[label] = narrative_id
                narrative_counter += 1

        # 4. For each valid narrative, compute mathematical centroid & pick canonical claim
        narratives_meta: Dict[str, Dict[str, Any]] = {}
        post_centroid_sims = {}

        for raw_label, narrative_id in raw_to_narrative_id.items():
            member_indices = np.where(raw_labels == raw_label)[0]
            member_embeddings = embeddings[member_indices]

            # Mathematical Centroid: Average vector of all posts in this cluster
            centroid = np.mean(member_embeddings, axis=0)
            norm = np.linalg.norm(centroid)
            if norm > 0:
                centroid = centroid / norm

            # Cosine similarity of each member to the cluster centroid
            member_sims = np.dot(member_embeddings, centroid)
            for idx, sim in zip(member_indices, member_sims):
                post_centroid_sims[idx] = float(sim)

            # The post closest to the centroid is our canonical representative claim!
            best_post_local_idx = int(np.argmax(member_sims))
            best_post_global_idx = member_indices[best_post_local_idx]
            canonical_post = posts[best_post_global_idx]

            unique_users = list({posts[idx].get("user_id", "unknown") for idx in member_indices})

            narratives_meta[narrative_id] = {
                "narrative_id": narrative_id,
                "canonical_claim": canonical_post["text"],
                "canonical_post_id": canonical_post["post_id"],
                "post_count": int(len(member_indices)),
                "unique_user_count": int(len(unique_users)),
                "users": unique_users,
                "mean_similarity": float(np.mean(member_sims))
            }

        # 5. Build enriched output posts
        annotated_posts = []
        for idx, post in enumerate(posts):
            raw_label = raw_labels[idx]
            narrative_id = raw_to_narrative_id.get(raw_label, None)
            sim_to_center = post_centroid_sims.get(idx, 1.0 if narrative_id is None else 0.0)

            annotated_posts.append({
                **post,
                "narrative_id": narrative_id,
                "centroid_similarity": round(float(sim_to_center), 4),
                "is_narrative": narrative_id is not None
            })

        return annotated_posts, narratives_meta
