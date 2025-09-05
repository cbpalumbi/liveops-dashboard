# populate_db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ml_liveops_dashboard.sqlite_models import Base
from ml_liveops_dashboard.db_utils import insert, clear, print as print_tables

# --- Create a SQLite database (in-memory or file) ---
engine = create_engine("sqlite:///../mab.db", echo=False)  
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# --- Create all tables from Base ---
Base.metadata.create_all(engine)

# --- Patch db_utils to use this session ---
import ml_liveops_dashboard.db_utils as db_utils
db_utils.session = session

# --- Clear segment-related tables first ---
clear("segment_mixes", db=session)
clear("segments", db=session)
clear("segment_mix_entries", db=session)
clear("segmented_mab_campaigns", db=session)

# --- Insert segment mix ---
insert("segment_mixes", {"name": "Platform Mix"}, db=session)

# --- Insert segments ---
insert("segments", {"name": "Mobile Users", "description": "", "rules_json": ""}, db=session)
insert("segments", {"name": "Other Users", "description": "", "rules_json": ""}, db=session)

# --- Insert segment mix entries ---
insert("segment_mix_entries", {"segment_mix_id": 1, "segment_id": 1, "percentage": 40}, db=session)
insert("segment_mix_entries", {"segment_mix_id": 1, "segment_id": 2, "percentage": 60}, db=session)

# --- Insert segmented MAB campaign ---
insert("segmented_mab_campaigns", {"segment_mix_id": 1}, db=session)

# --- Insert data campaign ---
insert(
    "data_campaigns",
    {
        "static_campaign_id": 1,
        "banner_id": 1,
        "campaign_type": "SEGMENTED_MAB",
        "segmented_mab_id": 1,
    },
    db=session,
)

# --- Print all tables to verify ---
print_tables(None, db=session)
