from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, JSON, Boolean
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

# --- SQLite Models ---
class DataCampaign(Base):
    __tablename__ = "data_campaigns"
    id = Column(Integer, primary_key=True, index=True)
    static_campaign_id = Column(Integer, nullable=False)
    tutorial_id = Column(Integer, nullable=False)
    campaign_type = Column(String, nullable=False)        # e.g. "MAB", "Random", "SEGMENTED_MAB"
    duration = Column(Integer, nullable=False)
    segment_mix_id = Column(Integer, nullable=True)     # NULL unless segmented MAB
    start_time = Column(DateTime,  nullable=True)
    end_time = Column(DateTime, nullable=True)

    simulation_result = relationship("SimulationResultModel", back_populates="campaign", uselist=False)
    
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Impression(Base):
    __tablename__ = "impressions"
    id = Column(Integer, primary_key=True, index=True)
    data_campaign_id = Column(Integer, nullable=False)    # Link to a data campaign run
    tutorial_id = Column(Integer, index=True, nullable=False)
    variant_id = Column(Integer, nullable=False)
    clicked = Column(Integer)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    segment = Column(Integer, nullable=True) 
    player_context = Column(String, nullable=True)  # JSON string for player context if needed 

class SegmentMix(Base):
    __tablename__ = "segment_mixes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    entries = relationship(
        "SegmentMixEntry", 
        back_populates="segment_mix", 
        cascade="all, delete-orphan"
    )

class SegmentMixEntry(Base):
    """
    Each SegmentMix consists of multiple SegmentMixEntries.
    Percentages should sum to 100 for a given segment_mix_id.
    """
    __tablename__ = "segment_mix_entries"
    id = Column(Integer, primary_key=True, index=True)
    segment_mix_id = Column(Integer, ForeignKey("segment_mixes.id"), nullable=False)
    segment_id = Column(Integer, ForeignKey("segments.id"), nullable=False)
    percentage = Column(Float, nullable=False)

    segment_mix = relationship("SegmentMix", back_populates="entries")

    segment = relationship("Segment", back_populates="segment_mix_entries")

class Segment(Base):
    __tablename__ = "segments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True) 
    rules_json = Column(String, nullable=True)   # optional JSON to define how segment is generated   

    segment_mix_entries = relationship(
        "SegmentMixEntry", 
        back_populates="segment",
    )

# modeled after SimulationResult in simulation utils
class SimulationResultModel(Base):
    __tablename__ = "simulation_results"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey('data_campaigns.id'))
    
    total_impressions = Column(Integer, nullable=False)
    cumulative_regret_mab = Column(Float, nullable=False)
    cumulative_regret_uniform = Column(Float, nullable=False)
    variant_counts = Column(JSON, nullable=False)
    completed = Column(Boolean, nullable=False)
    
    # optional campaign-specific fields
    per_segment_regret = Column(JSON, nullable=True)
    impression_log = Column(JSON, nullable=True)
    true_ctrs = Column(JSON, nullable=True)

    campaign = relationship("DataCampaign", back_populates="simulation_result")

class Tutorial(Base):
    __tablename__ = "tutorials"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    
    # 'variants' is a list of Variant objects associated with this tutorial
    variants = relationship("Variant", back_populates="tutorial", cascade="all, delete-orphan")

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Variant(Base):
    __tablename__ = "variants"

    id = Column(Integer, primary_key=True, index=True) 
    
    # refers to the index within the parent tutorial's list of variants
    json_id = Column(Integer, nullable=False) 
    
    name = Column(String, nullable=False)
    color = Column(String, nullable=True) # to be removed probably

    # link to tutorials table
    tutorial_id = Column(Integer, ForeignKey("tutorials.id"), nullable=False)

    tutorial = relationship("Tutorial", back_populates="variants")
    
    # Base CTR and Contextual Weights
    base_ctr = Column(Float, default=0.0) 
    base_params_weights_json = Column(String, default="{}") # Stored as JSON string
