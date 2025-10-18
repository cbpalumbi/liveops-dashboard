import hashlib
import json
import random
import numpy as np
from typing import Optional, Dict, List, Any, Union, Tuple
from collections import Counter, defaultdict
from dataclasses import dataclass, field

#TODO: Will be replaced by CTRs defined in data
def get_ctr_for_variant(static_campaign, tutorial_id, variant_id, segment_id=None,
                        min_ctr=0.05, max_ctr=0.4):
    for tutorial in static_campaign["tutorials"]:
        if tutorial["id"] == tutorial_id:
            for variant in tutorial["variants"]:
                if variant["id"] == variant_id:
                    # Base string includes segment_id if provided
                    variant_str = json.dumps({
                        "campaign_id": static_campaign["id"],
                        "tutorial_id": tutorial_id,
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

def get_true_params_for_variant(static_campaign, tutorial_id, variant_id):

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

    for tutorial in static_campaign["tutorials"]:
        if tutorial["id"] == tutorial_id:
            for variant in tutorial["variants"]:
                if variant["id"] == variant_id:
                    # Base string includes segment_id if provided
                    variant_str = json.dumps({
                        "campaign_id": static_campaign["id"],
                        "tutorial_id": tutorial_id,
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

LOGIT_SCALING_FACTOR = 0.1

def calculate_true_ctr_logistic(context_vector: np.ndarray, true_param_vector: np.ndarray):
    """
    Calculates the true click-through rate (CTR) using a logistic function.
    
    The dot product is multiplied by a scaling factor to prevent 
    CTR saturation near 1.0.
    """
    
    # 1. Calculate the linear predictor (logit)
    dot_product = np.dot(true_param_vector, context_vector)
    
    # 2. Apply the scaling factor to reduce the magnitude of the logit
    scaled_logit = dot_product * LOGIT_SCALING_FACTOR
    
    # 3. Apply the logistic function
    true_ctr = 1 / (1 + np.exp(-scaled_logit))
    
    return true_ctr

    
    return true_ctr

def load_static_campaigns():
    with open("ml_liveops_dashboard/data/static_tutorials.json", "r", encoding="utf-8") as f:
        return json.load(f)    

@dataclass
class SimulationResult:
    campaign_type: str
    total_impressions: int
    cumulative_regret_mab: float
    cumulative_regret_uniform: float
    variant_counts: Dict[int, int]
    completed: bool = False

    # Optional / campaign-specific fields
    per_segment_regret: Optional[Dict[int, Dict[str, Any]]] = field(default=None)
    impression_log: Optional[List[Dict[str, Any]]] = field(default=None)
    true_ctrs: Optional[Dict[int, float]] = field(default=None)

def generate_regret_summary (
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

        # if i % 10 == 0 or i == total_impressions:
        #     print(f"Impression {i}: Cumulative regret MAB = {cumulative_regret_mab:.3f}, Uniform = {cumulative_regret_uniform:.3f}")

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
        completed=True
    )


# Type hint for the segment-variant modifier structure, for clarity
SegmentVariantPerformanceMap = Dict[Tuple[int, int], float] 

def generate_regret_summary_segmented (
    impression_log: List[dict],
    base_ctrs: Dict[int, float],
    segment_variant_performance: SegmentVariantPerformanceMap, #(segment_id, variant_id) -> modifier
    campaign_type: str
) -> 'SimulationResult':
    """
    Calculates cumulative regret for a segmented MAB where the expected reward 
    (CTR) is unique for every (segment, variant) pair.

    The true CTRs are derived using the segment-variant specific additive modifier: 
    TrueCTR = BaseCTR + SegmentVariantModifier.

    Regret is calculated against the Segment-Specific Optimal Variant CTR.
    """

    # Extract all segment IDs present in the performance map
    all_segment_ids = {seg_id for seg_id, _ in segment_variant_performance.keys()}
    
    # Also include segments that appeared in the log, in case they were unconfigured 
    # (though they will use default 0.0 modifier)
    log_segment_ids = {imp.get("segment_id") for imp in impression_log if imp.get("segment_id") is not None}
    all_segment_ids.update(log_segment_ids)
    
    # Build the true_ctrs_map: {segment_id: {variant_id: TrueCTR}}
    true_ctrs_map = defaultdict(dict)
    
    for segment_id in all_segment_ids:
        for variant_id, base_ctr in base_ctrs.items():
            
            # Look up the specific modifier for this segment-variant pair, defaulting to 0.0
            lookup_key = (segment_id, variant_id)
            performance_modifier = segment_variant_performance.get(lookup_key, 0.0)
            
            # Calculate true CTR (BaseCTR + SegmentVariantModifier)
            true_ctr = base_ctr + performance_modifier
            
            # Clamp between 0.0 and 1.0 (CTR cannot be negative or > 1)
            true_ctr = max(0.0, min(1.0, true_ctr))
            
            true_ctrs_map[segment_id][variant_id] = true_ctr
    
    cumulative_regret_mab = 0.0
    cumulative_regret_uniform = 0.0
    total_impressions = len(impression_log)

    # Pre-calculate Segment-Specific Optimal CTRs and Uniform Baseline CTRs
    segment_optimum_ctrs: Dict[int, float] = {}
    segment_average_ctrs: Dict[int, float] = {}
    
    for segment_id, variant_ctrs in true_ctrs_map.items():
        if not variant_ctrs:
            continue
            
        # Optimal CTR for this segment (The best possible action)
        segment_optimum_ctrs[segment_id] = max(variant_ctrs.values())
        
        # Uniform Baseline (Average of all variant CTRs for this segment, 
        # representing uniform random allocation)
        segment_average_ctrs[segment_id] = sum(variant_ctrs.values()) / len(variant_ctrs)
        
    # For segmented campaigns, track impressions per segment
    segment_logs = defaultdict(list) if campaign_type == "segmented_mab" else None

    # --- Main Regret Loop ---
    for i, impression in enumerate(impression_log, 1):
        variant_id = impression["variant_id"]
        segment_id = impression.get("segment_id")
        
        # Ensure we have data for this segment
        if segment_id is None or segment_id not in true_ctrs_map:
            continue 

        # A. Optimal CTR for this specific segment
        optimal_ctr = segment_optimum_ctrs.get(segment_id, 0.0)
        
        # B. True CTR of the variant ACTUALLY served by the MAB
        actual_served_ctr = true_ctrs_map[segment_id].get(variant_id, 0.0) 

        # 1. MAB Regret (Optimal vs. Policy Action)
        mab_regret = optimal_ctr - actual_served_ctr
        cumulative_regret_mab += mab_regret

        # 2. Uniform Regret (Optimal vs. Uniform Baseline Action)
        uniform_baseline_ctr = segment_average_ctrs.get(segment_id, 0.0)
        uniform_regret_per_impression = optimal_ctr - uniform_baseline_ctr
        cumulative_regret_uniform += uniform_regret_per_impression

        # Track per-segment impressions
        if campaign_type == "segmented_mab" and segment_id is not None:
            segment_logs[segment_id].append(impression)

    # --- Output and Summary ---
    
    # Variant counts overall
    variant_ids = [entry["variant_id"] for entry in impression_log]
    counts = Counter(variant_ids)
    
    print("\nImpression counts per variant (Overall):")
    for variant_id, count in counts.items():
        print(f"Variant ID {variant_id}: {count} impressions")

    print(f"\nFinal cumulative regret after {total_impressions} impressions:")
    print(f"  MAB policy: {cumulative_regret_mab:.3f}")
    print(f"  Uniform random baseline: {cumulative_regret_uniform:.3f}")

    # Build per-segment results
    per_segment_regret = {}
    if campaign_type == "segmented_mab":
        print("\n--- Per-segment regret summary ---")
        for segment_id, logs in segment_logs.items():
            
            # Use pre-calculated segment-specific values
            seg_optimal_ctr = segment_optimum_ctrs.get(segment_id, 0.0)
            seg_uniform_ctr = segment_average_ctrs.get(segment_id, 0.0)
            
            # Recalculate MAB regret for the segment (Optimal - Served Variant's CTR)
            seg_cum_regret_mab = sum(
                seg_optimal_ctr - true_ctrs_map[imp["segment_id"]].get(imp["variant_id"], 0.0)
                for imp in logs
                if imp["segment_id"] in true_ctrs_map
            )
            
            # Recalculate Uniform regret for the segment (constant regret per impression * total impressions)
            regret_per_uniform_impression = seg_optimal_ctr - seg_uniform_ctr
            seg_cum_regret_uniform = regret_per_uniform_impression * len(logs)

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

    # The final returned object should reflect the overall cumulative regrets
    return SimulationResult(
        campaign_type=campaign_type,
        total_impressions=total_impressions,
        cumulative_regret_mab=cumulative_regret_mab,
        cumulative_regret_uniform=cumulative_regret_uniform,
        variant_counts=dict(counts),
        per_segment_regret=per_segment_regret,
        impression_log=impression_log,
        true_ctrs=true_ctrs_map, # Store the derived map
        completed=True
    )

def generate_regret_summary_contextual (
    impression_log: List[dict],
    true_param_vectors: Dict[int, np.ndarray]
) -> SimulationResult:
    """
    Generate a summary of the simulation results for a Contextual MAB campaign.
    
    Args:
        impression_log: A list of dictionaries, where each dict represents a served impression.
                        It must include 'variant_id' and 'player_context_vector'.
        true_param_vectors: A dictionary mapping variant_id to its true parameter vector.
        
    Returns:
        A SimulationResult object containing the summary data.
    """
    cumulative_regret_mab = 0.0
    cumulative_regret_uniform = 0.0
    total_impressions = len(impression_log)
    
    num_tutorials = len(true_param_vectors)
    uniform_prob = 1 / num_tutorials

    for i, impression in enumerate(impression_log, 1):
        variant_id = impression["variant_id"]
        player_context = impression["player_context_vector"]
        
        # --- 1. Calculate the true CTR for the chosen tutorial and this context ---
        chosen_tutorial_params = true_param_vectors[variant_id]
        true_ctr_mab = calculate_true_ctr_logistic(player_context, chosen_tutorial_params)

        # --- 2. Find the best possible CTR for this specific impression ---
        # This is what a perfect (oracle) model would have done
        optimal_ctr = 0.0
        for params in true_param_vectors.values():
            ctr = calculate_true_ctr_logistic(player_context, params)
            if ctr > optimal_ctr:
                optimal_ctr = ctr
        
        # --- 3. Calculate the average CTR for a uniform random policy ---
        # The uniform policy's expected CTR is the average of all possible CTRs
        # for this specific impression.
        expected_uniform_ctr = sum(
            calculate_true_ctr_logistic(player_context, params) * uniform_prob
            for params in true_param_vectors.values()
        )

        # --- 4. Calculate regrets ---
        # The regret for the MAB policy is the difference between the optimal
        # CTR and the CTR of the tutorial it actually chose.
        mab_regret = optimal_ctr - true_ctr_mab
        cumulative_regret_mab += mab_regret
        
        # The regret for the uniform policy is the difference between the optimal
        # CTR and the expected CTR of a random choice.
        uniform_regret = optimal_ctr - expected_uniform_ctr
        cumulative_regret_uniform += uniform_regret

        if i % 10 == 0 or i == total_impressions:
            print(f"Impression {i}: Cumulative regret MAB = {cumulative_regret_mab:.3f}, Uniform = {cumulative_regret_uniform:.3f}")

    # --- 5. Generate final summary metrics ---
    variant_ids = [entry["variant_id"] for entry in impression_log]
    counts = Counter(variant_ids)
    print("\nImpression counts per variant:")
    for variant_id, count in counts.items():
        print(f"Variant ID {variant_id}: {count} impressions")

    print(f"\nFinal cumulative regret after {total_impressions} impressions:")
    print(f"  Contextual MAB policy: {cumulative_regret_mab:.3f}")
    print(f"  Uniform random: {cumulative_regret_uniform:.3f}")

    print("Final Learned Weights: ", impression_log[-1]["currentLearnedWeights"])

    true_ctrs_summary = {}
    for vid, params in true_param_vectors.items():
        # For display purposes, calculate an average CTR across the whole log
        avg_ctr = np.mean([calculate_true_ctr_logistic(imp["player_context_vector"], params) for imp in impression_log])
        true_ctrs_summary[vid] = avg_ctr

    return SimulationResult(
        campaign_type="contextual_mab",
        total_impressions=total_impressions,
        cumulative_regret_mab=cumulative_regret_mab,
        cumulative_regret_uniform=cumulative_regret_uniform,
        variant_counts=dict(counts),
        per_segment_regret={}, # no segmented for contextual mab
        impression_log=impression_log,
        true_ctrs=true_ctrs_summary,
        completed=True
    )