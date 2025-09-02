import hashlib
import json
import random
import numpy as np
from typing import Optional, Dict, List, Any
from collections import Counter, defaultdict
from dataclasses import dataclass, field

#TODO: Will be replaced by CTRs defined in data
def get_ctr_for_variant(static_campaign, banner_id, variant_id, segment_id=None,
                        min_ctr=0.05, max_ctr=0.4):
    for banner in static_campaign["banners"]:
        if banner["id"] == banner_id:
            for variant in banner["variants"]:
                if variant["id"] == variant_id:
                    # Base string includes segment_id if provided
                    variant_str = json.dumps({
                        "campaign_id": static_campaign["id"],
                        "banner_id": banner_id,
                        "variant_id": variant_id,
                        "segment_id": segment_id,   # <--- key change
                        "color": variant.get("color")
                    }, sort_keys=True)
                    
                    h = hashlib.sha256(variant_str.encode()).hexdigest()
                    seed = int(h[:8], 16)
                    rng = random.Random(seed)
                    ctr = rng.uniform(min_ctr, max_ctr)
                    return ctr
    raise ValueError("Variant not found")

def get_true_params_for_variant(static_campaign, banner_id, variant_id):

    '''
    "player_context": {
            "player_id": 4,
            "age": 27,
            "region": "NA",
            "device_type": "Android",
            "sessions_per_day": 3,
            "avg_session_length": 13,
            "lifetime_spend": 2.83,
            "playstyle_vector": [0.622, 0.235, 0.143],
        },

    '''
    # 7 features

    # determine a 7 item array for each variant 

    for banner in static_campaign["banners"]:
        if banner["id"] == banner_id:
            for variant in banner["variants"]:
                if variant["id"] == variant_id:
                    # Base string includes segment_id if provided
                    variant_str = json.dumps({
                        "campaign_id": static_campaign["id"],
                        "banner_id": banner_id,
                        "variant_id": variant_id,
                        "color": variant.get("color")
                    }, sort_keys=True)
                    
                    h = hashlib.sha256(variant_str.encode()).hexdigest()
                    seed = int(h[:8], 16)
                    

                    variant_vector = []
                    for i in range(7):
                        rng = random.Random(seed)
                        variant_vector.append(rng.uniform(0.05, 0.8))
                        seed += 1

                    return variant_vector
    raise ValueError("Variant not found")

def calculate_true_ctr_logistic(context_vector: np.ndarray, true_param_vector: np.ndarray):
    """
    Calculates the true click-through rate (CTR) using a logistic function.
    
    Args:
        context_vector: A NumPy array representing the player's features.
        true_param_vector: A NumPy array representing the "true" parameters for a specific banner variant.
        
    Returns:
        The simulated true CTR, a value between 0 and 1.
    """
    
    print("context vector: ", context_vector)
    print("true_param_vector: ", true_param_vector)

    # Normalize context_vector with L2 norm
    norm_context = np.linalg.norm(context_vector)
    normalized_context = context_vector / norm_context if norm_context != 0 else np.zeros_like(context_vector)
    
    # Normalize true_param_vector with L2 norm
    norm_param = np.linalg.norm(true_param_vector)
    normalized_param = true_param_vector / norm_param if norm_param != 0 else np.zeros_like(true_param_vector)

    print("normalized context vector: ", normalized_context)
    print("normalized true_param_vector: ", normalized_param)
    
    # Calculate the dot product of the normalized vectors
    dot_product = np.dot(normalized_param, normalized_context)
    print("dot product (x) in logistic function is ", dot_product)
    
    # Apply the logistic function to map the result to a probability
    true_ctr = 1 / (1 + np.exp(-dot_product))
    
    return true_ctr



def load_static_campaigns():
    with open("ml_liveops_dashboard/src/data/campaigns.json", "r", encoding="utf-8") as f:
        return json.load(f)    

@dataclass
class SimulationResult:
    campaign_type: str
    total_impressions: int
    cumulative_regret_mab: float
    cumulative_regret_uniform: float
    variant_counts: Dict[int, int]

    # Optional / campaign-specific fields
    per_segment_regret: Optional[Dict[int, Dict[str, Any]]] = field(default=None)
    impression_log: Optional[List[Dict[str, Any]]] = field(default=None)
    true_ctrs: Optional[Dict[int, float]] = field(default=None)

def generate_regret_summary(
    impression_log: List[dict],
    true_ctrs: Dict[int, float],
    campaign_type: str
) -> SimulationResult:
    
    best_ctr = max(true_ctrs.values())
    cumulative_regret_mab = 0.0
    cumulative_regret_uniform = 0.0
    total_impressions = len(impression_log)
    uniform_prob = 1 / len(true_ctrs)

    # For segmented campaigns
    segment_logs = defaultdict(list) if campaign_type == "segmented_mab" else None

    for i, impression in enumerate(impression_log, 1):
        variant_id = impression["variant_id"]
        segment_id = impression.get("segment_id")

        # Overall regret
        mab_regret = best_ctr - true_ctrs[variant_id]
        cumulative_regret_mab += mab_regret
        expected_click_uniform = sum(ctr * uniform_prob for ctr in true_ctrs.values())
        cumulative_regret_uniform += best_ctr - expected_click_uniform

        # Track per-segment impressions
        if campaign_type == "segmented_mab" and segment_id is not None:
            segment_logs[segment_id].append(impression)

        if i % 10 == 0 or i == total_impressions:
            print(f"Impression {i}: Cumulative regret MAB = {cumulative_regret_mab:.3f}, Uniform = {cumulative_regret_uniform:.3f}")

    # Variant counts overall
    variant_ids = [entry["variant_id"] for entry in impression_log]
    counts = Counter(variant_ids)
    print("\nImpression counts per variant:")
    for variant_id, count in counts.items():
        print(f"Variant ID {variant_id}: {count} impressions")

    print(f"\nFinal cumulative regret after {total_impressions} impressions:")
    print(f"  MAB policy: {cumulative_regret_mab:.3f}")
    print(f"  Uniform random: {cumulative_regret_uniform:.3f}")

    # Build per-segment results
    per_segment_regret = {}
    if campaign_type == "segmented_mab":
        print("\n--- Per-segment regret summary ---")
        for segment_id, logs in segment_logs.items():
            seg_cum_regret_mab = sum(best_ctr - true_ctrs[imp["variant_id"]] for imp in logs)
            seg_cum_regret_uniform = sum(best_ctr - expected_click_uniform for _ in logs)

            # Count how many times each variant was shown for this segment
            variant_counts = Counter([imp["variant_id"] for imp in logs])

            # Print regret + impressions
            print(
                f"Segment {segment_id}: MAB regret = {seg_cum_regret_mab:.3f}, "
                f"Uniform regret = {seg_cum_regret_uniform:.3f}, "
                f"Impressions = {len(logs)}"
            )

            # Print per-variant allocation
            for vid, count in variant_counts.items():
                pct = (count / len(logs)) * 100
                print(f"  Variant {vid}: {count} impressions ({pct:.1f}%)")

            per_segment_regret[segment_id] = {
                "mab_regret": seg_cum_regret_mab,
                "uniform_regret": seg_cum_regret_uniform,
                "impressions": len(logs),
                "variant_counts": dict(variant_counts),
            }

    return SimulationResult(
        campaign_type=campaign_type,
        total_impressions=total_impressions,
        cumulative_regret_mab=cumulative_regret_mab,
        cumulative_regret_uniform=cumulative_regret_uniform,
        variant_counts=dict(counts),
        per_segment_regret=per_segment_regret,
        impression_log=impression_log,
        true_ctrs=true_ctrs,
    )
