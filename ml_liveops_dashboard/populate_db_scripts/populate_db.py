# populate_db.py
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime

from ml_liveops_dashboard.sqlite_models import Base
from ml_liveops_dashboard.db_utils import insert, clear, print as print_tables
import ml_liveops_dashboard.db_utils as db_utils
from constants import DB_PATH, TESTS_DB_PATH

def populate(db_path):
    # --- Patch db_utils to use this session ---
    engine = create_engine(db_path, echo=False)  
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    db_utils.session = session

    # --- Create all tables from Base ---
    Base.metadata.create_all(engine)

    # --- Clear segment-related tables first ---
    clear("segment_mixes", db=session)
    clear("segments", db=session)
    clear("segment_mix_entries", db=session)

    # --- Insert segment mix ---
    insert("segment_mixes", {"name": "Platform Mix"}, db=session)

    # --- Insert segments ---
    insert("segments", {"name": "Mobile Users", "description": "", "rules_json": ""}, db=session)
    insert("segments", {"name": "Other Users", "description": "", "rules_json": ""}, db=session)

    # --- Insert segment mix entries ---
    insert("segment_mix_entries", {"segment_mix_id": 1, "segment_id": 1, "percentage": 40}, db=session)
    insert("segment_mix_entries", {"segment_mix_id": 1, "segment_id": 2, "percentage": 60}, db=session)

    # --- Insert data campaign ---
    insert(
        "data_campaigns",
        {
            "static_campaign_id": 1,
            "tutorial_id": 1,
            "campaign_type": "SEGMENTED_MAB",
            "duration": 1,
            "segment_mix_id": 1,
            "start_time": datetime.datetime.now() # default for testing
        },
        db=session,
    )

    # --- Print all tables to verify ---
    print_tables(None, db=session)

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python populate_db.py --mode <dev|test>")
        sys.exit(1)

    # Check mode flag
    if sys.argv[1] != "--mode":
        print("First argument must be --mode")
        sys.exit(1)

    mode = sys.argv[2].lower()
    if mode not in ("dev", "test"):
        print("Mode must be either 'dev' or 'test'")
        sys.exit(1)
    
    if mode == "dev":
        populate(DB_PATH)
    else:
        populate(TESTS_DB_PATH)
