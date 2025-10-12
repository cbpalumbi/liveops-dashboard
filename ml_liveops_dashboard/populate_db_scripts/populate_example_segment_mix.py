# populate_example_segment_mix.py
# Adds a segment mix and related segment mix entries and segments. No campaigns.
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ml_liveops_dashboard.sqlite_models import Base
from ml_liveops_dashboard.db_utils import insert, clear
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

    print("\n--- POPULATE EX SEGMENT MIX: Inserting Example Segment Mix, Entries, and Segments ---")

    # --- Clear segment-related tables first ---
    clear("segment_mixes", db=session)
    clear("segments", db=session)
    clear("segment_mix_entries", db=session)

    # --- Insert segment mix ---
    insert("segment_mixes", {"name": "OS Mix"}, db=session)

    # --- Insert segments ---
    insert("segments", {"name": "iOS Users", "description": ""}, db=session)
    insert("segments", {"name": "Android Users", "description": ""}, db=session)

    # --- Insert segment mix entries ---
    insert("segment_mix_entries", {"segment_mix_id": 1, "segment_id": 1, "percentage": 25}, db=session)
    insert("segment_mix_entries", {"segment_mix_id": 1, "segment_id": 2, "percentage": 75}, db=session)

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python populate_example_segment_mix.py --mode <dev|test>")
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
