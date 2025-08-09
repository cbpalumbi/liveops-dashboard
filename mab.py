# Multi Armed Bandit
from sqlite_models import Impression
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
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

        if impressions == 0:
            # Exploration: immediately pick this variant. This ensures
            # that all variants are returned at least once
            return variant_id

        alpha = 1 + clicks
        beta = 1 + (impressions - clicks)
        score = random.betavariate(alpha, beta)
        variant_scores.append((variant_id, score))

    # Pick variant with max score
    print(f"DEBUG: Variants: {variant_scores}")
    best_variant = max(variant_scores, key=lambda x: x[1])[0]
    print(f"DEBUG: best variant {best_variant}\n")
    return best_variant

