from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import json
import uvicorn
import random

app = FastAPI()

# Load campaigns.json once on startup
with open("src/data/campaigns.json", "r", encoding="utf-8") as f:
    campaigns = json.load(f)

# Assign IDs dynamically for simplicity
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

@app.get("/campaigns", response_model=List[Campaign])
def get_campaigns():
    return campaigns

@app.get("/campaigns/{campaign_id}", response_model=Campaign)
def get_campaign(campaign_id: int):
    for c in campaigns:
        if c["id"] == campaign_id:
            return c
    raise HTTPException(status_code=404, detail="Campaign not found")

def pick_variant_randomly(banner):
    return random.choice(banner["variants"])

@app.post("/request-variants/{campaign_id}", response_model=RequestVariantsResponse)
def request_variants(campaign_id: int):
    campaign = next((c for c in campaigns if c["id"] == campaign_id), None)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    selections = []
    for banner in campaign.get("banners", []):
        variant = pick_variant_randomly(banner)
        # Increment impression count on serve
        variant["impressions"] += 1
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
        variant["successes"] += 1

    return ReportEventResponse(
        message="Event recorded",
        impressions=variant["impressions"],
        successes=variant["successes"],
    )
