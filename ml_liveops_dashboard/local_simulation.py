# local_simulation.py

import random
import time
from datetime import timedelta
import numpy as np
import json

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from ml_liveops_dashboard.ml_scripts.mab import (
    serve_variant,
    serve_variant_segmented,
    report_impression,
    player_context_json_to_vector,
    serve_variant_contextual
)
from ml_liveops_dashboard.simulation_utils import (
    SimulationResult, 
    generate_regret_summary, 
    generate_regret_summary_segmented,
    generate_regret_summary_contextual, 
    load_static_campaigns, 
    get_true_params_for_variant, 
    calculate_true_ctr_logistic
)
from ml_liveops_dashboard.sqlite_models import DataCampaign, Tutorial, SegmentMix, SegmentMixEntry
from ml_liveops_dashboard.generate_fake_players import generate_player

def run_mab_local(data_campaign_id: int, db, impressions: int = 50, delay: float = 0.02) -> SimulationResult:
    """Run a standard MAB campaign locally."""
    try:
        dc = db.query(DataCampaign).filter(DataCampaign.id == data_campaign_id).first()
        if not dc:
            print(f"DataCampaign {data_campaign_id} not found")
            return

        tutorial = db.query(Tutorial).options(selectinload(Tutorial.variants)).filter(Tutorial.id == dc.tutorial_id).first()
        if not tutorial:
            print(f"Tutorial not found in local DB")
            return None

        impression_log = []

        true_ctrs = {
            v.json_id: v.base_ctr
            for v in tutorial.variants
        }

        if dc.start_time is None:
            print("Simulation doesn't have a start time.")
            return

        if dc.end_time is None:
            # If end_time isn't defined, calculate it from start_time and duration
            end_time = dc.start_time + timedelta(minutes=dc.duration)
        else:
            end_time = dc.end_time

        duration_timedelta = end_time - dc.start_time
        if impressions > 1:
            time_step = duration_timedelta / impressions

        timestamp = dc.start_time

        for i in range(impressions):
            serve_data = serve_variant(dc, db)
            variant = serve_data["variant"]

            ctr = true_ctrs[variant.json_id]
            clicked = random.random() < ctr
            timestamp += time_step

            report_impression(data_campaign_id, variant.json_id, clicked, timestamp, db)

            impression_log.append({
                "variant_id": variant.json_id,
                "clicked": int(clicked)
            })

            #print(f"Impression {i+1}: variant {variant['name']} (id {variant['id']}), clicked: {clicked} (CTR={ctr:.2%})")
            if delay > 0:
                time.sleep(delay)

        return generate_regret_summary(impression_log, true_ctrs, campaign_type="mab")

    finally:
        db.close()



def run_segmented_mab_local(data_campaign_id: int, db, impressions: int = 50, delay: float = 0.02) -> 'SimulationResult':
    """
    Run a segmented MAB campaign locally.
    """
    try:
        # Load DataCampaign and its segment-variant modifiers
        dc = (
            db.query(DataCampaign)
            .options(selectinload(DataCampaign.segment_variant_modifiers)) # Eagerly load the segment variant modifiers
            .filter(DataCampaign.id == data_campaign_id)
            .first()
        )
        
        if not dc:
            print(f"DataCampaign {data_campaign_id} not found")
            return None

        # Load Tutorial and its variants
        query_result = db.query(Tutorial).options(selectinload(Tutorial.variants)).filter(Tutorial.id == dc.tutorial_id).first()
        if not query_result:
            print(f"Tutorial not found in local DB")
            return None
        tutorial = query_result

        impression_log = []

        base_ctrs = {
            v.json_id: v.base_ctr
            for v in tutorial.variants
        }

        # Load Segment Mix
        statement = (
            select(SegmentMix)
            .where(SegmentMix.id == dc.segment_mix_id)
            .options(
                selectinload(SegmentMix.entries)
                .selectinload(SegmentMixEntry.segment)
            )
        )
        
        segment_mix = db.execute(statement).scalar_one_or_none()
        
        if not segment_mix:
             print("Segment Mix not found for this campaign.")
             return None

        # Create a lookup table for Segment-Variant performance modifiers
        # Key: (segment_id, variant_id), Value: performance_modifier
        segment_variant_performance = {
            (p.segment_id, p.variant_id): p.performance_modifier
            for p in dc.segment_variant_modifiers
        }
        
        if not segment_variant_performance:
             print("Warning: Segment Variant Performance modifiers were not configured for this simulation.")


        # --- Time Initialization  ---
        if dc.start_time is None:
            print("Simulation doesn't have a start time.")
            return

        end_time = dc.end_time or (dc.start_time + timedelta(minutes=dc.duration))
        duration_timedelta = end_time - dc.start_time
        time_step = duration_timedelta / impressions if impressions > 1 else timedelta(minutes=0)
        timestamp = dc.start_time
        
        for i in range(impressions):
            serve_data = serve_variant_segmented(dc, db)
            variant = serve_data["variant"]
            segment_id = serve_data["segment_id"]
            
            variant_json_id = variant.json_id
            
            # Apply the segment-variant specific modifier
            segment_variant_lookup_key = (segment_id, variant_json_id)
            performance_modifier = segment_variant_performance.get(segment_variant_lookup_key, 0.0)

            ctr = base_ctrs[variant_json_id] + performance_modifier
            ctr = max(0.0, min(1.0, ctr)) # Clamp between 0 and 1
            
            clicked = random.random() < ctr
            timestamp += time_step

            report_impression(data_campaign_id, variant_json_id, clicked, timestamp, db, segment_id=segment_id)

            impression_log.append({
                "variant_id": variant_json_id,
                "clicked": int(clicked),
                "segment_id": segment_id
            })

            if delay > 0:
                time.sleep(delay)

        return generate_regret_summary_segmented(
            impression_log, 
            base_ctrs, 
            segment_variant_performance, 
            campaign_type="segmented_mab"
        )

    finally:
        db.close()

def run_contextual_mab_local(data_campaign_id: int, db, impressions: int = 5) -> SimulationResult:
    print("RUNNING CONTEXTUAL MAB LOCAL")

    try:
        
        dc = db.query(DataCampaign).filter(DataCampaign.id == data_campaign_id).first()
        if not dc:
            print(f"DataCampaign {data_campaign_id} not found")
            return

        tutorial = db.query(Tutorial).options(selectinload(Tutorial.variants)).filter(Tutorial.id == dc.tutorial_id).first()
        if not tutorial:
            print(f"Tutorial not found in local DB")
            return None

        impression_log = []

        # instead of determining true ctrs per variant here, i need to determine a 'true param vector' for each variant
        true_param_vectors = {
            v.json_id: np.array([
                float(x.strip()) 
                for x in v.base_params_weights_json.strip('{}').split(',')
            ], dtype=float)
            for v in tutorial.variants
        }

        if dc.start_time is None:
            print("Simulation doesn't have a start time.")
            return

        if dc.end_time is None:
            # If end_time isn't defined, calculate it from start_time and duration
            end_time = dc.start_time + timedelta(minutes=dc.duration)
        else:
            end_time = dc.end_time

        duration_timedelta = end_time - dc.start_time
        if impressions > 1:
            time_step = duration_timedelta / impressions

        timestamp = dc.start_time

        for i in range(impressions):
            simulated_player_context = generate_player(i)
            simulated_player_context_string = json.dumps(simulated_player_context)

            # serve
            serve_data = serve_variant_contextual(dc, db, simulated_player_context_string)
            served_variant_id = serve_data["variant"]

            # report
            player_context = player_context_json_to_vector(simulated_player_context_string) # TODO: Make variation on this function to accept json dict 
            
            # for each impressions calculate the probability of click based on the true_ctr_vector for the served variant 
                # and the context vector via a logistic function
            true_ctr = calculate_true_ctr_logistic(np.array(player_context), true_param_vectors[served_variant_id])
            
            # simulate click event
            clicked = random.random() < true_ctr
            timestamp += time_step
            report_impression(dc.id, served_variant_id, clicked, timestamp, db, None, simulated_player_context_string)
            
            impression_log.append({
                "variant_id": served_variant_id,
                "clicked": int(clicked),
                "player_context_vector": player_context,
            })

        return generate_regret_summary_contextual(impression_log, true_param_vectors)
    finally:
        db.close()

