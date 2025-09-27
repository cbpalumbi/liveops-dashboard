from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json

from ml_liveops_dashboard.sqlite_models import Base, DataCampaign, Impression, SegmentMix, SegmentMixEntry, Segment, SimulationResultModel
from ml_liveops_dashboard.ml_scripts.mab import (
    report_impression, 
    serve_variant, 
    serve_variant_segmented, 
    serve_variant_contextual
)
from constants import DB_PATH
from ml_liveops_dashboard.run_simulation import simulate_data_campaign
from ml_liveops_dashboard.simulation_utils import SimulationResult

engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
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
    duration: int # minutes
    segment_mix_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class CreateSegmentMixRequest(BaseModel):
    name: str

class CreateSegmentMixEntryRequest(BaseModel):
    segment_mix_id: int
    segment_id: int
    percentage: float

class CreateSegmentRequest(BaseModel):
    name: str
    description: Optional[str] = None
    rules_json: Optional[str] = None

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
    duration: int
    segment_mix_id: Optional[int] = None
    start_time: Optional[datetime]
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
    
class SegmentMixRequest(BaseModel):
    id: int
    name: str

class SegmentMixEntryRequest(BaseModel):
    id: int
    segment_mix_id: int
    segment_id: int
    percentage: float

class SegmentRequest(BaseModel):
    id: int
    name: str

class RunSimulationRequest(BaseModel):
    data_campaign_id: int
    impressions: int

class SimulationResultRequest(BaseModel):
    """
    Pydantic model for serializing a SimulationResultModel database object.
    It includes all fields from the SQLAlchemy model SimulationResultModel.
    """
    id: int
    campaign_id: int
    total_impressions: int
    cumulative_regret_mab: float
    cumulative_regret_uniform: float
    variant_counts: Dict[str, Any]
    per_segment_regret: Optional[Dict[str, Any]]
    impression_log: Optional[List[Dict[str, Any]]]
    true_ctrs: Optional[Dict[str, Any]]
    completed: bool
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
        campaign_type=req.campaign_type,
        duration=req.duration,
        segment_mix_id=req.segment_mix_id,
        start_time=req.start_time,
        end_time=req.end_time
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
    return imps

@app.get("/data_campaign/{data_campaign_id}", response_model=DataCampaignRequest)
def get_data_campaign(data_campaign_id: int, db: Session = Depends(get_db)):
    dc = db.query(DataCampaign).filter(DataCampaign.id == data_campaign_id).first()
    if not dc:
        raise HTTPException(status_code=404, detail="Data campaign not found")
    return dc

@app.get("/segment_mix/{segment_mix_id}", response_model=SegmentMixRequest)
def get_segment_mix(segment_mix_id: int, db: Session = Depends(get_db)):
    sm = db.query(SegmentMix).filter(SegmentMix.id == segment_mix_id).first()
    if not sm:
        raise HTTPException(status_code=404, detail="SegmentMix not found")
    return sm

@app.get("/segment_mixes", response_model=List[SegmentMixRequest])
def get_segment_mixes(db: Session = Depends(get_db)):
    sms = db.query(SegmentMix).all()
    return sms

@app.post("/segment_mix")
def create_data_campaign(req: CreateSegmentMixRequest, db: Session = Depends(get_db)):
    new_seg_mix = SegmentMix(
        name=req.name
    )
    db.add(new_seg_mix)
    db.commit()
    db.refresh(new_seg_mix)

    return {"status": "created", "segment_mix_id": new_seg_mix.id}

@app.get("/segment_mix_entries/{segment_mix_id}", response_model=List[SegmentMixEntryRequest])
def get_segment_mix_entries(segment_mix_id: int, db: Session = Depends(get_db)):
    entries = db.query(SegmentMixEntry).filter(SegmentMixEntry.segment_mix_id == segment_mix_id).all()
    return entries

@app.post("/segment_mix_entry")
def create_data_campaign(req: CreateSegmentMixEntryRequest, db: Session = Depends(get_db)):
    new_seg_mix_entry = SegmentMixEntry(
        segment_mix_id=req.segment_mix_id,
        segment_id=req.segment_id,
        percentage=req.percentage
    )
    db.add(new_seg_mix_entry)
    db.commit()
    db.refresh(new_seg_mix_entry)

    return {"status": "created", "segment_mix_entry_id": new_seg_mix_entry.id}

@app.get("/segment/{segment_id}", response_model=SegmentRequest)
def get_segment_mix(segment_id: int, db: Session = Depends(get_db)):
    segment = db.query(Segment).filter(Segment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    return segment

@app.get("/segments", response_model=List[SegmentRequest])
def get_segments(db: Session = Depends(get_db)):
    segments = db.query(Segment).all()
    return segments

@app.post("/segment")
def create_segment(req: CreateSegmentRequest, db: Session = Depends(get_db)):
    new_seg = Segment(
        name=req.name,
        description=req.description,
        rules_json=req.rules_json
    )
    db.add(new_seg)
    db.commit()
    db.refresh(new_seg)

    return {"status": "created", "segment_id": new_seg.id}

@app.post("/run_simulation", response_model=SimulationResult)
def run_simulation_from_frontend(req: RunSimulationRequest, db: Session = Depends(get_db)):
    dc = db.query(DataCampaign).filter(DataCampaign.id == req.data_campaign_id).first()
    if not dc:
        raise HTTPException(status_code=404, detail="Data campaign not found")
    
    current_time = datetime.now()
    end_time = current_time + timedelta(minutes=dc.duration)

    dc.start_time = current_time
    dc.end_time = end_time

    db.add(dc)
    db.commit()
    db.refresh(dc) 

    result = simulate_data_campaign(req.data_campaign_id, "local", req.impressions, 0.02)

    result_db_entry = SimulationResultModel(
        campaign_id=req.data_campaign_id,
        total_impressions=result.total_impressions,
        cumulative_regret_mab=result.cumulative_regret_mab,
        cumulative_regret_uniform=result.cumulative_regret_uniform,
        completed=True,
        variant_counts=result.variant_counts,
        per_segment_regret=result.per_segment_regret,
        impression_log=result.impression_log,
        true_ctrs=result.true_ctrs
    )
    
    db.add(result_db_entry)
    db.commit()
    db.refresh(result_db_entry) 
    
    return result

@app.get("/simulation_result/{data_campaign_id}", response_model=Optional[SimulationResultRequest])
def get_simulation_result(data_campaign_id: int, db: Session = Depends(get_db)):
    simulation_result = db.query(SimulationResultModel).filter(SimulationResultModel.campaign_id == data_campaign_id).first()
    return simulation_result

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

