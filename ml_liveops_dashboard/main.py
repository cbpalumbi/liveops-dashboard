from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session ,selectinload
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from constants import DB_PATH
from ml_liveops_dashboard.sqlite_models import (
    Base, 
    DataCampaign,
    Impression,
    SegmentMix, 
    SegmentMixEntry, 
    Segment, 
    SimulationResultModel,
    Tutorial,
    Variant
)
from ml_liveops_dashboard.ml_scripts.mab import (
    report_impression, 
    serve_variant, 
    serve_variant_segmented, 
    serve_variant_contextual
)
from ml_liveops_dashboard.run_simulation import simulate_data_campaign
from ml_liveops_dashboard.simulation_utils import SimulationResult
from ml_liveops_dashboard.populate_db_scripts.populate_tutorials import populate as populate_tutorials

engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base.metadata.create_all(bind=engine)

# --- App ---
app = FastAPI()
populate_tutorials(DB_PATH)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()        

# --- Pydantic models ---
class CreateDataCampaignRequest(BaseModel):
    campaign_id: int
    tutorial_id: int
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
    segment_ctr_modifier: float
    description: Optional[str] = None

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

class SegmentRequest(BaseModel):
    id: int
    name: str
    segment_ctr_modifier: float
    model_config = {
        "from_attributes": True 
    }

class SegmentMixEntryRequest(BaseModel):
    id: int
    segment_mix_id: int
    segment_id: int
    percentage: float
    segment: Optional[SegmentRequest] = None
    model_config = {
        "from_attributes": True 
    }
    
class SegmentMixRequest(BaseModel):
    id: int
    name: str
    entries: Optional[List[SegmentMixEntryRequest]] = None
    model_config = {
        "from_attributes": True 
    }

class VariantRequest(BaseModel):
    id: int
    json_id: int # refers to the index this occupies within its parent tutorial's variant list
    name: str
    color: str
    base_ctr: float
    base_params_weights_json: str # for contextual MAB
    model_config = {
        "from_attributes": True
    }

class TutorialRequest(BaseModel):
    id: int
    title: str
    variants: List[VariantRequest]
    model_config = {
        "from_attributes": True
    }

class DataCampaignRequest(BaseModel):
    id: int
    static_campaign_id: int
    campaign_type: str
    duration: int
    tutorial_id: int
    tutorial: Optional[TutorialRequest] = None
    segment_mix_id: Optional[int] = None
    segment_mix: Optional[SegmentMixRequest] = None
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    model_config = {
        "from_attributes": True
    }

class ImpressionRequest(BaseModel):
    data_campaign_id: int
    tutorial_id: int
    variant_id: int
    clicked: bool
    segment: Optional[int] = None
    player_context: Optional[str] = None
    timestamp: datetime
    model_config = {
        "from_attributes": True
    }

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

class PatchVariantRequest(BaseModel):
    base_ctr: Optional[float] = Field(None, ge=0.0, le=1.0) # Ensures 0 <= CTR <= 1
    base_params_weights_json: str

# --- Endpoint to create a data campaign ---
@app.post("/data_campaign")
def create_data_campaign(req: CreateDataCampaignRequest, db: Session = Depends(get_db)):
    # TODO: validate that the tutorial requested actually exists in the db
    
    # Insert into DB
    new_campaign = DataCampaign(
        static_campaign_id=req.campaign_id,
        tutorial_id=req.tutorial_id,
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
    # Note: does not eager load any of the associated data (Tutorial, Segment Mix)

    dcs = db.query(DataCampaign).all()
    return dcs

@app.get("/tutorials")
def get_tutorials(db: Session = Depends(get_db), response_model=List[TutorialRequest]):
    tutorials = (
        db.query(Tutorial)
        .options(selectinload(Tutorial.variants)) # loads in variant table - bypasses lazy loading
        .all()
    )
    return tutorials

@app.get("/tutorials/{campaign_id}")
def get_tutorial(campaign_id: int, db: Session = Depends(get_db), response_model=TutorialRequest):
    tutorial = (
        db.query(Tutorial)
        .options(selectinload(Tutorial.variants)) 
        .filter(Tutorial.id == campaign_id)
        .first() 
    )
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial not found")
    return tutorial

@app.patch("/variant/{variant_id}")
def patch_tutorial_variant(req: PatchVariantRequest, variant_id: int, db: Session = Depends(get_db), response_model=VariantRequest):
    variant = db.query(Variant).filter(Variant.id == variant_id).first()
    
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")

    if req.base_ctr is not None:
        variant.base_ctr = req.base_ctr
        variant.base_params_weights_json = req.base_params_weights_json

    db.commit()
    db.refresh(variant)
    
    return variant

@app.get("/impressions/{data_campaign_id}", response_model=List[ImpressionRequest])
def get_impressions(data_campaign_id: int, db: Session = Depends(get_db)):
    imps = db.query(Impression).filter(Impression.data_campaign_id == data_campaign_id).all()
    return imps

@app.get("/data_campaign/{data_campaign_id}", response_model=DataCampaignRequest)
def get_data_campaign(data_campaign_id: int, db: Session = Depends(get_db)):
    dc = db.query(DataCampaign).filter(DataCampaign.id == data_campaign_id).first()
    if not dc:
        raise HTTPException(status_code=404, detail="Data campaign not found")
    
    # Eager load Tutorial obj 
    tutorial = (
        db.query(Tutorial)
        .options(selectinload(Tutorial.variants)) 
        .filter(Tutorial.id == dc.tutorial_id)
        .first() 
    )
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial not found")
    
    tutorial_data = TutorialRequest.model_validate(tutorial)
    
    # Eager load segment mix information if this is a segmented MAB campaign
    segment_mix_data = None
    
    if dc.segment_mix_id:
        statement = (
            select(SegmentMix)
            .options(
                selectinload(SegmentMix.entries)
                .selectinload(SegmentMixEntry.segment)
            )
            .where(SegmentMix.id == dc.segment_mix_id)
        )

        sm = db.execute(statement).scalars().first()
        if sm:
            segment_mix_data = SegmentMixRequest.model_validate(sm)
        
    response_data = dc.__dict__.copy() 
    response_data.pop('_sa_instance_state', None)
    
    # Add manually processed fields
    response_data["segment_mix"] = segment_mix_data
    response_data["tutorial"] = tutorial_data
    
    return response_data

@app.get("/segment_mix/{segment_mix_id}", response_model=SegmentMixRequest)
def get_segment_mix(segment_mix_id: int, db: Session = Depends(get_db)):
    # Note: Eager loads the corresponding segment mix entries and segments
    statement = (
        select(SegmentMix)
        .options(
            selectinload(SegmentMix.entries)
            .selectinload(SegmentMixEntry.segment)
        )
        .where(SegmentMix.id == segment_mix_id)
    )

    sm = db.execute(statement).scalars().first()

    if not sm:
        raise HTTPException(status_code=404, detail="SegmentMix not found")
    return sm

@app.get("/segment_mixes", response_model=List[SegmentMixRequest])
def get_segment_mixes(db: Session = Depends(get_db)):
    # Returns all segment mixes and eager loads their segment mix entries and segments 
    
    statement = (
        select(SegmentMix)
        .options(
            selectinload(SegmentMix.entries)
            .selectinload(SegmentMixEntry.segment)
        )
    )
    
    result = db.execute(statement).scalars().all()
    
    return result

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
def create_segment_mix_entry(req: CreateSegmentMixEntryRequest, db: Session = Depends(get_db)):
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
        segment_ctr_modifier=req.segment_ctr_modifier,
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

    result = simulate_data_campaign(req.data_campaign_id, "local", req.impressions, 0)

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

