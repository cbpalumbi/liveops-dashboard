from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

# --- SQLite Models ---
class DataCampaign(Base):
    __tablename__ = "data_campaigns"
    id = Column(Integer, primary_key=True, index=True)
    static_campaign_id = Column(Integer, nullable=False)
    banner_id = Column(Integer, nullable=False)
    campaign_type = Column(String, nullable=False)        # e.g. "MAB", "Random", "SEGMENTED_MAB"
    segmented_mab_id = Column(Integer, nullable=True)     # NULL unless segmented MAB
    start_time = Column(DateTime, server_default=func.now())
    end_time = Column(DateTime, nullable=True)

class Impression(Base):
    __tablename__ = "impressions"
    id = Column(Integer, primary_key=True, index=True)
    data_campaign_id = Column(Integer, nullable=False)    # Link to a data campaign run
    banner_id = Column(Integer, index=True, nullable=False)
    variant_id = Column(Integer, nullable=False)
    clicked = Column(Integer)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class Segment(Base):
    __tablename__ = "segments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    #description = Column(String, nullable=True)  # could store notes about segment definition
    #rules_json = Column(String, nullable=True)   # optional JSON to define how segment is generated

class SegmentMix(Base):
    __tablename__ = "segment_mixes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

class SegmentMixEntry(Base):
    """
    Each SegmentMix consists of multiple SegmentMixEntries.
    Percentages should sum to 100 for a given segment_mix_id.
    """
    __tablename__ = "segment_mix_entries"
    id = Column(Integer, primary_key=True, index=True)
    segment_mix_id = Column(Integer, nullable=False)
    segment_id = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)

class SegmentedMABCampaign(Base):
    __tablename__ = "segmented_mab_campaigns"
    id = Column(Integer, primary_key=True, index=True)
    segment_mix_id = Column(Integer, nullable=False)
    #notes = Column(String, nullable=True)  


