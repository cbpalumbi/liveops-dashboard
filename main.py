from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from pydantic import BaseModel
import json

from sqlite_models import DataCampaign
from mab import report_impression, serve_variant

DATABASE_URL = "sqlite:///./mab.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

Base.metadata.create_all(bind=engine)

# --- Load static campaign JSON ---
with open("src/data/campaigns.json", "r", encoding="utf-8") as f:
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

class ServeRequest(BaseModel):
    data_campaign_id: int

class ReportRequest(BaseModel):
    data_campaign_id: int
    variant_id: int
    clicked: bool

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

@app.get("/data_campaign/{data_campaign_id}")
def get_data_campaign(data_campaign_id: int, db: Session = Depends(get_db)):
    dc = db.query(DataCampaign).filter(DataCampaign.id == data_campaign_id).first()
    if not dc:
        raise HTTPException(status_code=404, detail="Data campaign not found")
    return dc

@app.get("/data_campaigns")
def get_data_campaigns(db: Session = Depends(get_db)):
    dcs = db.query(DataCampaign).all()
    if not dcs:
        raise HTTPException(status_code=404, detail="Data campaign not found")
    return dcs


# --- Serve Endpoint ---
@app.post("/serve")
def serve_variant_api(req: ServeRequest, db: Session = Depends(get_db)):
    try:
        return serve_variant(req.data_campaign_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    

@app.post("/report")
def report_impression_api(req: ReportRequest, db: Session = Depends(get_db)):
    try:
        return report_impression(req.data_campaign_id, req.variant_id, req.clicked, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- Frontend Endpoints ---
@app.get("/campaigns")
def get_campaigns():
    return static_campaigns

@app.get("/campaigns/{campaign_id}")
def get_campaign(campaign_id: int):
    for c in static_campaigns:
        if c["id"] == campaign_id:
            return c
    raise HTTPException(status_code=404, detail="Campaign not found")