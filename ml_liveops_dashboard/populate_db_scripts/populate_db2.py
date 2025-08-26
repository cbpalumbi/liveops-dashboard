# populate_db2.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ml_liveops_dashboard.sqlite_models import Base
from ml_liveops_dashboard.db_utils import insert, print as print_tables

# --- Create a SQLite database (in-memory or file) ---
engine = create_engine("sqlite:///../mab.db", echo=False)  
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# --- Create all tables from Base ---
Base.metadata.create_all(engine)

# --- Patch db_utils to use this session ---
import ml_liveops_dashboard.db_utils as db_utils
db_utils.session = session

# --- Insert data campaign ---
insert(
    "camp",
    {
        "static_campaign_id": 1,  # assuming your static campaign exists
        "banner_id": 1,           # the banner you want to test
        "campaign_type": "MAB",   # regular MAB type
        "segmented_mab_id": None  # not used for regular MAB
    },
)

# --- Print all tables to verify ---
print_tables(None)
