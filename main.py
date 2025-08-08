import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import json
import random

app = FastAPI()

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# load static campaign data once on startup.
# TODO: Move to a db. Will also need to store links to imgs 
with open("src/data/campaigns.json", "r", encoding="utf-8") as f:
    campaigns = json.load(f)

# Assign IDs dynamically for simplicity - will be replaced
for i, campaign in enumerate(campaigns):
    campaign["id"] = i + 1
    for j, banner in enumerate(campaign.get("banners", [])):
        banner["id"] = j + 1
        for k, variant in enumerate(banner.get("variants", [])):
            variant["id"] = k + 1
            # Add some basic stats placeholders for MAB, start at zero
            variant.setdefault("impressions", 0)
            variant.setdefault("successes", 0)
            variant.setdefault("failures", 0)

# Pydantic models
class Variant(BaseModel):
    id: int
    name: str
    color: str
    impressions: int
    successes: int
    failures: int

class Banner(BaseModel):
    id: int
    title: str
    variants: List[Variant]

class Campaign(BaseModel):
    id: int
    name: str
    banners: List[Banner]

# represents the variant selection for a single banner within a campaign
class VariantSelection(BaseModel):
    banner_id: int
    variant_id: int
    variant_name: str

# retrieves one variant per banner within a campaign
class RequestVariantsResponse(BaseModel):
    campaign_id: int
    selections: List[VariantSelection]

# represents a click on a banner variant
class ReportEventRequest(BaseModel):
    campaign_id: int
    banner_id: int
    variant_id: int
    clicked: bool

# what the model tracks. an impression is when a user is shown the banner.
# it's a success if they actually clicked on it
class ReportEventResponse(BaseModel):
    message: str
    impressions: int
    successes: int

# --------- HELPERS ---------

def pick_variant_randomly(banner):
    return random.choice(banner["variants"])

# Helper to generate Redis keys for stats
def impressions_key(campaign_id, banner_id, variant_id):
    return f"stats:{campaign_id}:{banner_id}:{variant_id}:impressions"

def successes_key(campaign_id, banner_id, variant_id):
    return f"stats:{campaign_id}:{banner_id}:{variant_id}:successes"

# --------- ENDPOINTS ---------


@app.get("/campaigns", response_model=List[Campaign])
def get_campaigns():
    return campaigns

@app.get("/campaigns/{campaign_id}", response_model=Campaign)
def get_campaign(campaign_id: int):
    for c in campaigns:
        if c["id"] == campaign_id:
            return c
    raise HTTPException(status_code=404, detail="Campaign not found")

@app.post("/request-variants/{campaign_id}", response_model=RequestVariantsResponse)
def request_variants(campaign_id: int):
    campaign = next((c for c in campaigns if c["id"] == campaign_id), None)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    selections = []
    for banner in campaign.get("banners", []):
        variant = pick_variant_randomly(banner)

        # Increment impression count on serve
        r.incr(impressions_key(campaign_id, banner["id"], variant["id"]))

        selections.append(
            VariantSelection(
                banner_id=banner["id"],
                variant_id=variant["id"],
                variant_name=variant["name"],
            )
        )

    return RequestVariantsResponse(campaign_id=campaign_id, selections=selections)

@app.post("/report-event", response_model=ReportEventResponse)
def report_event(event: ReportEventRequest):
    campaign = next((c for c in campaigns if c["id"] == event.campaign_id), None)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    banner = next((b for b in campaign.get("banners", []) if b["id"] == event.banner_id), None)
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")

    variant = next((v for v in banner.get("variants", []) if v["id"] == event.variant_id), None)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")

    if event.clicked:
        r.incr(successes_key(event.campaign_id, event.banner_id, event.variant_id))
    
    impressions = int(r.get(impressions_key(event.campaign_id, event.banner_id, event.variant_id)) or 0)
    successes = int(r.get(successes_key(event.campaign_id, event.banner_id, event.variant_id)) or 0)

    return ReportEventResponse(
        message="Event recorded",
        impressions=impressions,
        successes=successes,
    )
