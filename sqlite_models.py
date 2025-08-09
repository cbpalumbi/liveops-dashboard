from sqlalchemy import Column, Integer, Boolean, String, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

# --- SQLite Models ---
class DataCampaign(Base):
    __tablename__ = "data_campaigns"
    id = Column(Integer, primary_key=True, index=True)
    static_campaign_id = Column(Integer, nullable=False)  # from campaigns.json
    banner_id = Column(Integer, nullable=False)
    campaign_type = Column(String, nullable=False)        # e.g. "MAB", "Random"
    start_time = Column(DateTime, server_default=func.now())
    end_time = Column(DateTime, nullable=True)

class Impression(Base):
    __tablename__ = "impressions"
    id = Column(Integer, primary_key=True, index=True)
    data_campaign_id = Column(Integer, nullable=False)    # Link to a data campaign run
    banner_id = Column(Integer, index=True, nullable=False)
    variant_id = Column(Integer, nullable=False)
    clicked = Column(Boolean, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
