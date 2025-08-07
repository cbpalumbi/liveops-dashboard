from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
import uvicorn

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

@app.get("/campaigns", response_model=List[Campaign])
def get_campaigns():
    return campaigns

@app.get("/campaigns/{campaign_id}", response_model=Campaign)
def get_campaign(campaign_id: int):
    for c in campaigns:
        if c["id"] == campaign_id:
            return c
    raise HTTPException(status_code=404, detail="Campaign not found")
