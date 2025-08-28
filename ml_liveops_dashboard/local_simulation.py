# local_simulation.py

import random
import time
from datetime import datetime, timedelta, timezone

from ml_liveops_dashboard.main import SessionLocal
from ml_liveops_dashboard.ml_scripts.mab import (
    serve_variant,
    serve_variant_segmented,
    report_impression
)
from ml_liveops_dashboard.simulation_utils import SimulationResult, generate_regret_summary, get_ctr_for_variant, load_static_campaigns, get_ctr_vector_for_variant
from ml_liveops_dashboard.sqlite_models import DataCampaign

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
        
        # instead of determining true ctrs per variant here, i need to determine a linear expression for each variant
        for variant in static_banner_variants_ids:
            print("HELLO: ", get_ctr_vector_for_variant(static_campaign, banner_id, variant))

    
        # need to generate new players - can use same script as before maybe? 
        player1={
            "data_campaign_id": data_campaign_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "player_context": {
                "player_id": 3,
                "age": 27,
                "region": "NA",
                "device_type": "Android",
                "sessions_per_day": 3,
                "avg_session_length": 13,
                "lifetime_spend": 2.83,
                "playstyle_vector": [0.622, 0.235, 0.143],
            }
        }

        #for i in range(impressions):

            # serve

            # report
        
    finally:

        db.close()


    return