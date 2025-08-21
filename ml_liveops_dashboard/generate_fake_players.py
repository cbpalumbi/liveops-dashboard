import argparse
import json
import random
import uuid
import numpy as np

REGIONS = ["NA", "EU", "ASIA", "LATAM"]
DEVICES = ["iOS", "Android", "Tablet"]

def generate_playstyle_vector(dim=3):
    """Generate a normalized playstyle vector using Dirichlet distribution."""
    return np.random.dirichlet(np.ones(dim)).round(3).tolist()

def generate_player(player_id: int):
    return {
        "player_id": player_id,
        "age": random.randint(13, 50),  # game demo range
        "region": random.choice(REGIONS),
        "device_type": random.choice(DEVICES),
        "sessions_per_day": max(1, int(np.random.poisson(2))),  # most players 1–3
        "avg_session_length": int(np.random.normal(20, 10)),    # mean 20 mins, variance
        "lifetime_spend": round(max(0, np.random.exponential(5)), 2),  # skewed distribution
        "playstyle_vector": generate_playstyle_vector(),
    }

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic player profiles.")
    parser.add_argument("--output", type=str, required=True, help="Output JSON file name")
    parser.add_argument("--num_players", type=int, required=True, help="Number of players to generate")
    args = parser.parse_args()

    players = [generate_player(i) for i in range(1, args.num_players + 1)]

    with open(args.output, "w") as f:
        json.dump(players, f, indent=2)

    print(f"✅ Generated {args.num_players} players → {args.output}")

if __name__ == "__main__":
    main()
