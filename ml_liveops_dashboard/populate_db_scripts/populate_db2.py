# populate_db2.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime
import sys

from ml_liveops_dashboard.sqlite_models import Base
from ml_liveops_dashboard.db_utils import insert, print as print_tables
from constants import DB_PATH, TESTS_DB_PATH

def populate(db_path):
    # --- Create a SQLite database (in-memory or file) ---
    engine = create_engine(db_path, echo=False)  
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
            "tutorial_id": 1,           # the tutorial you want to test
            "campaign_type": "MAB",   # regular MAB type
            "duration": 1,
            "segment_mix_id": None,  # not used for regular MAB
            "start_time": datetime.datetime.now() # default for testing
        },
    )

    # --- Print all tables to verify ---
    print_tables(None)


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

