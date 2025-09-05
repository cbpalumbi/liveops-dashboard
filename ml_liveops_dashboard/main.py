from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
import json

from ml_liveops_dashboard.sqlite_models import Base, DataCampaign, Impression
from ml_liveops_dashboard.ml_scripts.mab import report_impression, serve_variant, serve_variant_segmented, serve_variant_contextual

DATABASE_URL = "sqlite:///../mab.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base.metadata.create_all(bind=engine)

# --- Load static campaign JSON ---
with open("ml_liveops_dashboard/src/data/campaigns.json", "r", encoding="utf-8") as f:
    static_campaigns = json.load(f)

# --- App ---
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Pydantic models ---
class CreateDataCampaignRequest(BaseModel):
    campaign_id: int
    banner_id: int
    campaign_type: str

class PlayerContext(BaseModel): # Used for contextual MAB campaigns
    player_id: int
    age: int = Field(..., ge=0, le=120)
    region: str
    device_type: str
    sessions_per_day: int = Field(..., ge=0)
    avg_session_length: int = Field(..., ge=0)  # minutes
    lifetime_spend: float = Field(..., ge=0.0)
    playstyle_vector: List[float] = Field(..., min_length=3, max_length=3)

class ServeRequest(BaseModel):
    data_campaign_id: int
    timestamp: datetime
    player_context: Optional[PlayerContext] = None

class ReportRequest(BaseModel):
    data_campaign_id: int
    variant_id: int
    clicked: bool
    segment_id: Optional[int] = None
    timestamp: datetime
    player_context: Optional[PlayerContext] = None

class DataCampaignRequest(BaseModel):
    id: int
    static_campaign_id: int
    banner_id: int
    campaign_type: str
    start_time: datetime
    end_time: Optional[datetime]
    model_config = {
        "from_attributes": True
}

class ImpressionRequest(BaseModel):
    data_campaign_id: int
    banner_id: int
    variant_id: int
    clicked: bool
    segment: Optional[int] = None
    player_context: Optional[str] = None
    timestamp: datetime
    model_config = {
        "from_attributes": True
}


# --- Helpers ---
def validate_static_campaign(campaign_id: int, banner_id: int):
    for campaign in static_campaigns:
        if campaign["id"] == campaign_id:
            for banner in campaign["banners"]:
                if banner["id"] == banner_id:
                    return True
            raise HTTPException(status_code=400, detail="Banner not found in this campaign")
    raise HTTPException(status_code=404, detail="Static campaign not found")

# --- Endpoint to create a data campaign ---
@app.post("/data_campaign")
def create_data_campaign(req: CreateDataCampaignRequest, db: Session = Depends(get_db)):
    # Validate campaign exists in static data
    validate_static_campaign(req.campaign_id, req.banner_id)

    # Insert into DB
    new_campaign = DataCampaign(
        static_campaign_id=req.campaign_id,
        banner_id=req.banner_id,
        campaign_type=req.campaign_type
    )
    db.add(new_campaign)
    db.commit()
    db.refresh(new_campaign)

    return {"status": "created", "data_campaign_id": new_campaign.id}


@app.get("/data_campaigns")
def get_data_campaigns(db: Session = Depends(get_db)):
    dcs = db.query(DataCampaign).all()
    return dcs

@app.get("/campaigns")
def get_campaigns():
    return static_campaigns

@app.get("/campaigns/{campaign_id}")
def get_campaign(campaign_id: int):
    for c in static_campaigns:
        if c["id"] == campaign_id:
            return c
    raise HTTPException(status_code=404, detail="Campaign not found")

@app.get("/impressions/{data_campaign_id}", response_model=List[ImpressionRequest])
def get_impressions(data_campaign_id: int, db: Session = Depends(get_db)):
    imps = db.query(Impression).filter(Impression.data_campaign_id == data_campaign_id).all()
    #print("imps ",imps)
    return imps

@app.get("/data_campaign/{data_campaign_id}", response_model=DataCampaignRequest)
def get_data_campaign(data_campaign_id: int, db: Session = Depends(get_db)):
    dc = db.query(DataCampaign).filter(DataCampaign.id == data_campaign_id).first()
    if not dc:
        raise HTTPException(status_code=404, detail="Data campaign not found")
    #print(dc)
    return dc

# --- MAB Endpoints ---
@app.post("/serve")
def serve_variant_api(req: ServeRequest, db: Session = Depends(get_db)):
    dc = db.query(DataCampaign).filter(DataCampaign.id == req.data_campaign_id).first()
    if not dc:
        raise HTTPException(status_code=404, detail="Data campaign not found")

    try:
        # Route by campaign type
        campaign_type = dc.campaign_type.lower()
        if campaign_type == "mab":
            return serve_variant(dc, db)  # original single MAB
        
        elif campaign_type == "segmented_mab":
            return serve_variant_segmented(dc, db)
        
        elif campaign_type == "contextual_mab":
            if req.player_context:
                # Convert PlayerContext to JSON string for storage
                player_context_json = req.player_context.model_dump_json()
            else:
                player_context_json = None  # Ensure it's None if not provided
            return serve_variant_contextual(dc, db, player_context=player_context_json)
            
        else:
            # fallback to random variant serving via normal /serve
            # TODO: change this to route to its own function not in mab.py
            return serve_variant(dc, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/report")
def report_impression_api(req: ReportRequest, db: Session = Depends(get_db)):
    try:
        if req.player_context:
            # Convert PlayerContext to JSON string for storage
            player_context_json = req.player_context.model_dump_json()
        else:
            player_context_json = None  # Ensure it's None if not provided

        return report_impression(req.data_campaign_id, req.variant_id, req.clicked, req.timestamp, db, segment_id=req.segment_id, player_context=player_context_json)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

