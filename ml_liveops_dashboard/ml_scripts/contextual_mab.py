# contextual_mab.py

import os
import joblib
import numpy as np
from typing import List

MODEL_PATH = "player_clusters.joblib"
_kmeans_model = None

# Lazy-load with existence check
if os.path.exists(MODEL_PATH):
    _kmeans_model = joblib.load(MODEL_PATH)
else:
    print(f"Warning: clustering model file not found at {MODEL_PATH}. "
          f"Did you run the pretraining script?")

def get_cluster_id(feature_vector: List[float]) -> int:
    """
    Given a numeric feature vector for a player, return the cluster ID
    from the pretrained KMeans model.

    Args:
        feature_vector (List[float]): Player features as a flat list of floats/ints.

    Returns:
        int: The cluster ID assigned by KMeans.
    """
    if _kmeans_model is None:
        raise RuntimeError("Clustering model not loaded. Please train and save it first.")

    vector_np = np.array(feature_vector).reshape(1, -1)
    cluster_id = int(_kmeans_model["model"].predict(vector_np)[0])
    return cluster_id
