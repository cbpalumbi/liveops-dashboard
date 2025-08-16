import hashlib
import json
import random
from collections import Counter, defaultdict

def get_ctr_for_variant(static_campaign, banner_id, variant_id, min_ctr=0.05, max_ctr=0.3):
    for banner in static_campaign["banners"]:
        if banner["id"] == banner_id:
            for variant in banner["variants"]:
                if variant["id"] == variant_id:
                    variant_str = json.dumps({
                        "campaign_id": static_campaign["id"],
                        "banner_id": banner_id,
                        "variant_id": variant_id,
                        "color": variant.get("color")
                    }, sort_keys=True)
                    h = hashlib.sha256(variant_str.encode()).hexdigest()
                    seed = int(h[:8], 16)
                    rng = random.Random(seed)
                    ctr = rng.uniform(min_ctr, max_ctr)
                    return ctr
    raise ValueError("Variant not found")

def load_static_campaigns():
    with open("src/data/campaigns.json", "r", encoding="utf-8") as f:
        return json.load(f)    

def print_regret_summary(impression_log, true_ctrs, campaign_type):
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

    # Additional per-segment regret summary for segmented MAB
    if campaign_type == "segmented_mab":
        print("\n--- Per-segment regret summary ---")
        for segment_id, logs in segment_logs.items():
            seg_cum_regret_mab = sum(best_ctr - true_ctrs[imp["variant_id"]] for imp in logs)
            seg_cum_regret_uniform = sum(best_ctr - expected_click_uniform for _ in logs)
            print(f"Segment {segment_id}: MAB regret = {seg_cum_regret_mab:.3f}, Uniform regret = {seg_cum_regret_uniform:.3f}, Impressions = {len(logs)}")