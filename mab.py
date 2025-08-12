# Multi Armed Bandit
from sqlite_models import Impression
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import datetime
import random, json

from sqlite_models import DataCampaign

# --- Load static campaign JSON ---
with open("src/data/campaigns.json", "r", encoding="utf-8") as f:
    static_campaigns = json.load(f)

def get_static_banner_variants(static_campaign_id: int, banner_id: int) -> list[int]:
    static_campaign = next((c for c in static_campaigns if c["id"] == static_campaign_id), None)
    if not static_campaign:
        raise ValueError(f"Static campaign id {static_campaign_id} not found")

    banner = next((b for b in static_campaign["banners"] if b["id"] == banner_id), None)
    if not banner:
        raise ValueError(f"Banner id {banner_id} not found in static campaign {static_campaign_id}")

    return [variant["id"] for variant in banner["variants"]]

def run_thompson_sampling(data_campaign_id: int, banner_id: int, db: Session):
    # Get static campaign id for this data campaign
    dc = db.query(DataCampaign).filter(DataCampaign.id == data_campaign_id).first()
    if not dc:
        raise ValueError("Data campaign not found")

    static_banner_variants = get_static_banner_variants(dc.static_campaign_id, banner_id)

    variant_scores = []

    zero_impression_variants = [
        vid for vid in static_banner_variants
        if db.query(func.count(Impression.id)).filter(
            Impression.data_campaign_id == data_campaign_id,
            Impression.banner_id == banner_id,
            Impression.variant_id == vid
        ).scalar() == 0
    ]

    if zero_impression_variants:
        return random.choice(zero_impression_variants)

    for variant_id in static_banner_variants:
        clicks = db.query(func.sum(Impression.clicked)).filter(
            Impression.data_campaign_id == data_campaign_id,
            Impression.banner_id == banner_id,
            Impression.variant_id == variant_id
        ).scalar() or 0

        impressions = db.query(func.count(Impression.id)).filter(
            Impression.data_campaign_id == data_campaign_id,
            Impression.banner_id == banner_id,
            Impression.variant_id == variant_id
        ).scalar() or 0

        alpha = 1 + clicks
        beta = 1 + (impressions - clicks)
        score = random.betavariate(alpha, beta)
        variant_scores.append((variant_id, score))

    best_variant = max(variant_scores, key=lambda x: x[1])[0]
    return best_variant

# --- Serve Logic (can be used by API endpoint or local function) ---
def serve_variant(data_campaign_id: int, db: Session):
    dc = db.query(DataCampaign).filter(DataCampaign.id == data_campaign_id).first()
    if not dc:
        raise ValueError("Data campaign not found")

    static_campaign = next((c for c in static_campaigns if c["id"] == dc.static_campaign_id), None)
    if not static_campaign:
        raise ValueError("Static campaign not found")

    banner = next((b for b in static_campaign["banners"] if b["id"] == dc.banner_id), None)
    if not banner:
        raise ValueError("Banner not found in static campaign")

    # Variant Selection Logic
    if dc.campaign_type.lower() == "mab":
        variant_id = run_thompson_sampling(dc.id, banner["id"], db)
        chosen_variant = next(v for v in banner["variants"] if v["id"] == variant_id)
    else:
        chosen_variant = random.choice(banner["variants"])

    return {
        "data_campaign_id": data_campaign_id,
        "static_campaign_id": dc.static_campaign_id,
        "banner_id": banner["id"],
        "variant": chosen_variant
    }

# --- Report Impression Core Logic (can be used by API endpoint or local function) ---
def report_impression(data_campaign_id: int, variant_id: int, clicked: bool, timestamp: datetime, db: Session):
    dc = db.query(DataCampaign).filter(DataCampaign.id == data_campaign_id).first()
    if not dc:
        raise ValueError("Data campaign not found")

    # Store impression in SQLite
    impression = Impression(
        data_campaign_id=data_campaign_id,
        banner_id=dc.banner_id,
        variant_id=variant_id,
        clicked=clicked,
        timestamp=timestamp
    )
    db.add(impression)
    db.commit()

    return {"status": "logged"}