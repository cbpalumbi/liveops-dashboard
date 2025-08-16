# Multi Armed Bandit
from sqlite_models import Impression
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import datetime
import random, json

from sqlite_models import DataCampaign, SegmentedMABCampaign, SegmentMix, SegmentMixEntry

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
def serve_variant(dc: DataCampaign, db: Session):
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
        "data_campaign_id": dc.id,
        "static_campaign_id": dc.static_campaign_id,
        "banner_id": banner["id"],
        "variant": chosen_variant
    }

# --- Report Impression Core Logic (can be used by API endpoint or local function) ---
def report_impression(
    data_campaign_id: int,
    variant_id: int,
    clicked: bool,
    timestamp: datetime,
    db: Session,
    segment_id: int = None 
):
    """
    Store an impression in the database.
    If segment_id is provided, it will be recorded for segmented MAB campaigns.
    """
    from sqlite_models import DataCampaign, Impression

    dc = db.query(DataCampaign).filter(DataCampaign.id == data_campaign_id).first()
    if not dc:
        raise ValueError("Data campaign not found")

    # Store impression in SQLite
    impression = Impression(
        data_campaign_id=data_campaign_id,
        banner_id=dc.banner_id,
        variant_id=variant_id,
        clicked=clicked,
        timestamp=timestamp,
        segment=segment_id  # will be None for non-segmented campaigns
    )
    db.add(impression)
    db.commit()

    return {"status": "logged"}


def run_thompson_sampling_segmented(data_campaign_id: int, banner_id: int, segment_id: int, db: Session):
    """
    Run Thompson Sampling for a specific segment.
    """
    # Get static campaign id for this data campaign
    dc = db.query(DataCampaign).filter(DataCampaign.id == data_campaign_id).first()
    if not dc:
        raise ValueError("Data campaign not found")

    static_banner_variants = get_static_banner_variants(dc.static_campaign_id, banner_id)

    variant_scores = []

    # Find variants with zero impressions in this segment
    zero_impression_variants = [
        vid for vid in static_banner_variants
        if db.query(func.count(Impression.id)).filter(
            Impression.data_campaign_id == data_campaign_id,
            Impression.banner_id == banner_id,
            Impression.variant_id == vid,
            Impression.segment == segment_id  # filter by segment
        ).scalar() == 0
    ]

    if zero_impression_variants:
        return random.choice(zero_impression_variants)

    # Calculate Thompson Sampling score per variant
    for variant_id in static_banner_variants:
        clicks = db.query(func.sum(Impression.clicked)).filter(
            Impression.data_campaign_id == data_campaign_id,
            Impression.banner_id == banner_id,
            Impression.variant_id == variant_id,
            Impression.segment == segment_id  # filter by segment
        ).scalar() or 0

        impressions = db.query(func.count(Impression.id)).filter(
            Impression.data_campaign_id == data_campaign_id,
            Impression.banner_id == banner_id,
            Impression.variant_id == variant_id,
            Impression.segment == segment_id  # filter by segment
        ).scalar() or 0

        alpha = 1 + clicks
        beta = 1 + (impressions - clicks)
        score = random.betavariate(alpha, beta)
        variant_scores.append((variant_id, score))

    # Return the variant with highest sampled score
    best_variant = max(variant_scores, key=lambda x: x[1])[0]
    return best_variant

def serve_variant_segmented(dc: DataCampaign, db: Session):
    """
    Serve a variant for a campaign using Segmented MAB.
    Randomly assigns the impression to a segment according to the segment_mix,
    then runs Thompson Sampling for that segment.
    Returns chosen variant and segment info.
    """

    # Get segmented MAB config
    smab = db.query(SegmentedMABCampaign).filter(
        SegmentedMABCampaign.data_campaign_id == data_campaign_id
    ).first()
    if not smab:
        raise ValueError("Segmented MAB config not found for this campaign")

    # Load segment mix and entries
    segment_mix = db.query(SegmentMix).filter(SegmentMix.id == smab.segment_mix_id).first()
    if not segment_mix:
        raise ValueError("Segment mix not found")

    entries = db.query(SegmentMixEntry).filter(SegmentMixEntry.segment_mix_id == segment_mix.id).all()
    if not entries:
        raise ValueError("No entries found for segment mix")

    # Randomly assign segment based on percentages
    total_weight = sum(e.percentage for e in entries)
    rnd = random.uniform(0, total_weight)
    cumulative = 0
    selected_segment = entries[0].segment_id  # default fallback
    for entry in entries:
        cumulative += entry.percentage
        if rnd <= cumulative:
            selected_segment = entry.segment_id
            break

    # Run Thompson Sampling for the selected segment
    variant_id = run_thompson_sampling_segmented(dc.id, dc.banner_id, selected_segment, db)

    # Get static campaign info for variant details
    with open("src/data/campaigns.json", "r", encoding="utf-8") as f:
        static_campaigns = json.load(f)
    static_campaign = next((c for c in static_campaigns if c["id"] == dc.static_campaign_id), None)
    if not static_campaign:
        raise ValueError("Static campaign not found")

    banner = next((b for b in static_campaign["banners"] if b["id"] == dc.banner_id), None)
    if not banner:
        raise ValueError("Banner not found in static campaign")

    chosen_variant = next(v for v in banner["variants"] if v["id"] == variant_id)

    return {
        "data_campaign_id": dc.id,
        "static_campaign_id": dc.static_campaign_id,
        "banner_id": dc.banner_id,
        "segment_id": selected_segment,
        "variant": chosen_variant
    }
