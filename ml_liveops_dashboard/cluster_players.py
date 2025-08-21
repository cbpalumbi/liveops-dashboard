#!/usr/bin/env python3
import argparse
import json
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import joblib

def load_players(input_file):
    with open(input_file, "r") as f:
        return json.load(f)

def players_to_vectors(players):
    """Convert list of players to numeric feature vectors."""
    vectors = []
    for p in players:
        vec = [
            p["age"],
            p["sessions_per_day"],
            p["avg_session_length"],
            p["lifetime_spend"],
        ] + p["playstyle_vector"]
        vectors.append(vec)
    return np.array(vectors)

def main():
    parser = argparse.ArgumentParser(description="Cluster player profiles with KMeans.")
    parser.add_argument("--input", type=str, required=True, help="Input JSON file of players")
    parser.add_argument("--output", type=str, required=True, help="Output file for trained model (.joblib)")
    parser.add_argument("--clusters", type=int, default=5, help="Number of clusters (default=5)")
    args = parser.parse_args()

    # Load & prepare data
    players = load_players(args.input)
    X = players_to_vectors(players)

    # Normalize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train clustering model
    kmeans = KMeans(n_clusters=args.clusters, random_state=42, n_init="auto")
    kmeans.fit(X_scaled)

    # Save model + scaler
    joblib.dump({"scaler": scaler, "model": kmeans}, args.output)

    # Print summary
    labels, counts = np.unique(kmeans.labels_, return_counts=True)
    print("✅ Clustering complete")
    print(f"   Input players: {len(players)}")
    print(f"   Number of clusters: {args.clusters}")
    print(f"   Inertia (lower=better fit): {kmeans.inertia_:.2f}")
    print("   Cluster sizes:")
    for l, c in zip(labels, counts):
        print(f"     Cluster {l}: {c} players")

if __name__ == "__main__":
    main()
