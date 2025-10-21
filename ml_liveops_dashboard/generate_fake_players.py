import numpy as np
import argparse
import random
import json

REGIONS = ["NA", "EU", "ASIA"]
DEVICES = ["mobile", "tablet", "desktop"]

# --- Normalization Ranges ---
NORMALIZATION_RANGES = {
    "age": {"min": 13, "max": 50},
    # Set a practical max for Poisson(2) to cap outliers, 8 covers P > 99.8%
    "sessions_per_day": {"min": 1, "max": 8}, 
    # Set a practical max for Normal(20, 10). 3-sigma (50) is reasonable, using 60.
    "avg_session_length": {"min": 0, "max": 60}, 
    # Set a practical max for Exponential(5). 4x mean is 20.
    "lifetime_spend": {"min": 0, "max": 20.0},
}

def normalize_value(key: str, value: float) -> float:
    """Applies Min-Max scaling to a single numerical value based on predefined ranges."""
    if key not in NORMALIZATION_RANGES:
        # If no range is defined (e.g., playstyle vector elements, which are handled separately)
        return value

    min_val = NORMALIZATION_RANGES[key]["min"]
    max_val = NORMALIZATION_RANGES[key]["max"]

    if max_val <= min_val:
        return 0.0  # Avoid division by zero, return 0 if range is invalid

    # Clamp the value to the defined range before scaling
    clamped_value = max(min_val, min(max_val, value))
    
    # Min-Max Scaling: (x - min) / (max - min)
    return (clamped_value - min_val) / (max_val - min_val)


def generate_playstyle_vector(dim=3):
    """Generate a normalized playstyle vector using Dirichlet distribution."""
    return np.random.dirichlet(np.ones(dim)).round(3).tolist()

def generate_player(player_id: int):
    """
    Generates a player profile and normalizes all numerical features to [0, 1].
    """
    # --- Generate raw values ---
    raw_session_length = int(np.clip(np.random.normal(20, 10), 5, 60))

    sessions_per_day = max(1, int(np.random.poisson(2)))

    # Incorporate sessions per day into lifetime spend so more active players are more likely to spend more
    lifetime_spend = round(
        max(0, np.random.exponential(3 + 0.5 * sessions_per_day)), 2
    )
    
    player_data = {
        "player_id": player_id,
        "age": random.randint(13, 50),
        "region": random.choice(REGIONS),
        "device_type": random.choice(DEVICES),
        "sessions_per_day": sessions_per_day,
        "avg_session_length": raw_session_length, 
        "lifetime_spend": lifetime_spend,
        "playstyle_vector": generate_playstyle_vector(),
    }
    
    # --- Normalize numerical fields ---
    
    # Age
    player_data["age_normalized"] = normalize_value("age", player_data["age"])
    
    # Sessions Per Day
    player_data["sessions_per_day_normalized"] = normalize_value("sessions_per_day", player_data["sessions_per_day"])
    
    # Average Session Length
    player_data["avg_session_length_normalized"] = normalize_value("avg_session_length", player_data["avg_session_length"])
    
    # Lifetime Spend
    player_data["lifetime_spend_normalized"] = normalize_value("lifetime_spend", player_data["lifetime_spend"])
    
    return player_data

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic player profiles.")
    parser.add_argument("--output", type=str, required=True, help="Output JSON file name")
    parser.add_argument("--num_players", type=int, required=True, help="Number of players to generate")
    args = parser.parse_args()

    players = [generate_player(i) for i in range(1, args.num_players + 1)]

    with open(args.output, "w") as f:
        json.dump(players, f, indent=2)

    print(f"Generated {args.num_players} players → {args.output}")

if __name__ == "__main__":
    main()
