# local_simulation.py

import random
import time
from datetime import datetime, timedelta, timezone
import numpy as np
import json

from ml_liveops_dashboard.main import SessionLocal
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
    generate_regret_summary_contextual,
    get_ctr_for_variant, 
    load_static_campaigns, 
    get_true_params_for_variant, 
    calculate_true_ctr_logistic
)
from ml_liveops_dashboard.sqlite_models import DataCampaign
from ml_liveops_dashboard.generate_fake_players import generate_player

def run_mab_local(data_campaign_id: int, impressions: int = 50, delay: float = 0.02) -> SimulationResult:
    """Run a standard MAB campaign locally."""
    db = SessionLocal()
    try:
        dc = db.query(DataCampaign).filter(DataCampaign.id == data_campaign_id).first()
        if not dc:
            print(f"DataCampaign {data_campaign_id} not found")
            return

        static_campaigns = load_static_campaigns()
        static_campaign = next((c for c in static_campaigns if c["id"] == dc.static_campaign_id), None)
        if not static_campaign:
            print("Static campaign for data campaign not found")
            return

        impression_log = []
        banner_id = dc.banner_id

        static_banner_variants = [
            v["id"] for b in static_campaign["banners"] if b["id"] == banner_id for v in b["variants"]
        ]
        true_ctrs = {
            variant_id: get_ctr_for_variant(static_campaign, banner_id, variant_id)
            for variant_id in static_banner_variants
        }

        timestamp = datetime.now(timezone.utc) - timedelta(weeks=1)

        for i in range(impressions):
            serve_data = serve_variant(dc, db)
            variant = serve_data["variant"]

            ctr = true_ctrs[variant["id"]]
            clicked = random.random() < ctr
            timestamp += timedelta(minutes=1)

            report_impression(data_campaign_id, variant["id"], clicked, timestamp, db)

            impression_log.append({
                "variant_id": variant["id"],
                "clicked": int(clicked)
            })

            print(f"Impression {i+1}: variant {variant['name']} (id {variant['id']}), clicked: {clicked} (CTR={ctr:.2%})")
            time.sleep(delay)

        return generate_regret_summary(impression_log, true_ctrs, campaign_type="mab")

    finally:
        db.close()



def run_segmented_mab_local(data_campaign_id: int, impressions: int = 50, delay: float = 0.02) -> SimulationResult:
    """Run a segmented MAB campaign locally."""
    db = SessionLocal()
    try:
        dc = db.query(DataCampaign).filter(DataCampaign.id == data_campaign_id).first()
        if not dc:
            print(f"DataCampaign {data_campaign_id} not found")
            return

        static_campaigns = load_static_campaigns()
        static_campaign = next((c for c in static_campaigns if c["id"] == dc.static_campaign_id), None)
        if not static_campaign:
            print("Static campaign for data campaign not found")
            return

        impression_log = []
        banner_id = dc.banner_id

        static_banner_variants = [
            v["id"] for b in static_campaign["banners"] if b["id"] == banner_id for v in b["variants"]
        ]
        true_ctrs = {
            variant_id: get_ctr_for_variant(static_campaign, banner_id, variant_id)
            for variant_id in static_banner_variants
        }

        timestamp = datetime.now(timezone.utc) - timedelta(weeks=1)

        for i in range(impressions):
            serve_data = serve_variant_segmented(dc, db)
            variant = serve_data["variant"]
            segment_id = serve_data["segment_id"]

            ctr = true_ctrs[variant["id"]]
            clicked = random.random() < ctr
            timestamp += timedelta(minutes=1)

            report_impression(data_campaign_id, variant["id"], clicked, timestamp, db, segment_id=segment_id)

            impression_log.append({
                "variant_id": variant["id"],
                "clicked": int(clicked),
                "segment_id": segment_id
            })

            print(f"Impression {i+1}: variant {variant['name']} (id {variant['id']}), "
                  f"segment {segment_id}, clicked: {clicked} (CTR={ctr:.2%})")
            time.sleep(delay)

        return generate_regret_summary(impression_log, true_ctrs, campaign_type="segmented_mab")

    finally:
        db.close()

def run_contextual_mab_local(data_campaign_id: int, impressions: int = 5):
    print("RUNNING CONTEXTUAL MAB LOCAL")

    db = SessionLocal()

    try:
        
        dc = db.query(DataCampaign).filter(DataCampaign.id == data_campaign_id).first()
        if not dc:
            print(f"DataCampaign {data_campaign_id} not found")
            return

        static_campaigns = load_static_campaigns()
        static_campaign = next((c for c in static_campaigns if c["id"] == dc.static_campaign_id), None)
        if not static_campaign:
            print("Static campaign for data campaign not found")
            return

        impression_log = []
        banner_id = dc.banner_id

        static_banner_variants_ids = [
            v["id"] for b in static_campaign["banners"] if b["id"] == banner_id for v in b["variants"]
        ]

        # instead of determining true ctrs per variant here, i need to determine a 'true param vector' for each variant
        true_param_vectors = {
            variant_id: np.array(get_true_params_for_variant(static_campaign, banner_id, variant_id))
            for variant_id in static_banner_variants_ids
        }

        timestamp = datetime.now(timezone.utc) - timedelta(weeks=1)

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
            timestamp += timedelta(minutes=1)
            report_impression(dc.id, served_variant_id, clicked, timestamp, db, None, simulated_player_context_string)
            
            impression_log.append({
                "variant_id": served_variant_id,
                "clicked": int(clicked),
                "player_context_vector": player_context,
            })

        return generate_regret_summary_contextual(impression_log, true_param_vectors)
        
    finally:
        db.close()


    return