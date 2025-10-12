from ml_liveops_dashboard.run_simulation import simulate_data_campaign
from ml_liveops_dashboard.simulation_utils import SimulationResult
from ml_liveops_dashboard.populate_db_scripts.populate_test_segMAB import populate as populate_test_segMAB 
from ml_liveops_dashboard.populate_db_scripts.populate_test_MAB import populate as populate_test_MAB
from constants import TESTS_DB_PATH

def test_mab_simulation_flow():
    
    populate_test_MAB(TESTS_DB_PATH)

    result = simulate_data_campaign(1, mode="local", impressions=100, db_path=TESTS_DB_PATH)
    assert isinstance(result, SimulationResult)
    assert result.cumulative_regret_mab < 2 * result.cumulative_regret_uniform, \
        "MAB regret should no more than half of uniform random regret"
    assert len(result.impression_log) == 100
    assert set(result.variant_counts.keys()) == {1, 2, 3}

# Define expected IDs based on the corrected populate_segMAB script (Tutorial 0, Variants 1 and 2)
SEGMENT_ID_MOBILE = 1 
SEGMENT_ID_OTHER = 2
VARIANT_ID_V1 = 1 # Expected winner for Mobile (0.20 CTR)
VARIANT_ID_V2 = 2 # Expected winner for Other (0.25 CTR)

def test_segmented_mab_simulation_flow(test_db_session):

    # Populate DB with Segment-Variant specific data 
    populate_test_segMAB(TESTS_DB_PATH)

    # Run simulation
    TOTAL_IMPRESSIONS = 750
    # Data Campaign ID is explicitly 1 from the setup script
    result = simulate_data_campaign(1, mode="local", impressions=TOTAL_IMPRESSIONS, db_path=TESTS_DB_PATH)

    # Basic Assertions
    assert isinstance(result, SimulationResult)
    assert len(result.impression_log) == TOTAL_IMPRESSIONS
    assert result.campaign_type == "segmented_mab"
    
    # Assert that the overall MAB policy is better than the overall uniform baseline
    # The factor 0.8 is a safety margin for randomness
    assert result.cumulative_regret_mab < 0.8 * result.cumulative_regret_uniform, \
        "Overall Segmented MAB regret must be significantly lower than Uniform Baseline regret."

    # Contextual Assertions (Per-Segment Performance)
    
    # Ensure all segments were processed and we only have the correct 2 variants
    assert set(result.variant_counts.keys()) == {VARIANT_ID_V1, VARIANT_ID_V2}, "Should only use variants 1 and 2"
    assert SEGMENT_ID_MOBILE in result.per_segment_regret.keys()
    assert SEGMENT_ID_OTHER in result.per_segment_regret.keys()
    
    # --- Assertions for Segment 1 (Mobile Users) ---
    seg1_result = result.per_segment_regret[SEGMENT_ID_MOBILE]
    v1_count_mobile = seg1_result["variant_counts"].get(VARIANT_ID_V1, 0)
    v2_count_mobile = seg1_result["variant_counts"].get(VARIANT_ID_V2, 0)
    
    # Expected Winner: V1 (0.20 CTR)
    
    # Rule 1: MAB must beat uniform for this segment
    assert seg1_result["mab_regret"] < 0.8 * seg1_result["uniform_regret"], \
        f"Segment {SEGMENT_ID_MOBILE} (Mobile) MAB regret must be lower than Uniform regret."
    
    # Rule 2: Segment MAB should serve the optimal variant (V1) significantly more often
    assert v1_count_mobile > 2 * v2_count_mobile, \
        f"Segment {SEGMENT_ID_MOBILE} should favor Variant {VARIANT_ID_V1} (Optimal: 0.20 CTR)."
    
    # --- Assertions for Segment 2 (Other Users) ---
    seg2_result = result.per_segment_regret[SEGMENT_ID_OTHER]
    v1_count_other = seg2_result["variant_counts"].get(VARIANT_ID_V1, 0)
    v2_count_other = seg2_result["variant_counts"].get(VARIANT_ID_V2, 0)

    # Expected Winner: V2 (0.25 CTR)
    
    # Rule 1: MAB must beat uniform for this segment
    assert seg2_result["mab_regret"] < 0.8 * seg2_result["uniform_regret"], \
        f"Segment {SEGMENT_ID_OTHER} (Other) MAB regret must be lower than Uniform regret."

    # Rule 2: Segment MAB should serve the optimal variant (V2) significantly more often
    assert v2_count_other > 2 * v1_count_other, \
        f"Segment {SEGMENT_ID_OTHER} should favor Variant {VARIANT_ID_V2} (Optimal: 0.25 CTR)."

