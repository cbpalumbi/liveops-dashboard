# populate_test_segMAB.py
# Used in tests for segmented MAB
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from ml_liveops_dashboard.sqlite_models import Base
from ml_liveops_dashboard.db_utils import insert, clear, print as print_tables
from ml_liveops_dashboard.populate_db_scripts.populate_tutorials import populate as populate_tutorials
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

    populate_tutorials(db_path, "ml_liveops_dashboard/data/test_segMAB_tutorials.json")

    # --- Clear segment-related tables first ---
    clear("segment_mixes", db=session)
    clear("segments", db=session)
    clear("segment_mix_entries", db=session)
    clear("segment_variant_performance", db=session) 

    # --- Constants for consistency ---
    DATA_CAMPAIGN_ID = 1
    TUTORIAL_ID = 0 
    SEGMENT_ID_MOBILE = 1 
    SEGMENT_ID_OTHER = 2   
    VARIANT_ID_V1 = 1 # Option A (Base CTR 0.1)
    VARIANT_ID_V2 = 2 # Option B (Base CTR 0.2)

    # --- Insert segment mix ---
    insert("segment_mixes", {"name": "Platform Mix"}, db=session)

    # --- Insert segments ---
    insert("segments", {"name": "Mobile Users", "description": ""}, db=session)
    insert("segments", {"name": "Other Users", "description": ""}, db=session)

    # --- Insert segment mix entries ---
    insert("segment_mix_entries", {"segment_mix_id": 1, "segment_id": SEGMENT_ID_MOBILE, "percentage": 40}, db=session)
    insert("segment_mix_entries", {"segment_mix_id": 1, "segment_id": SEGMENT_ID_OTHER, "percentage": 60}, db=session)

    # --- Insert data campaign ---
    insert(
        "data_campaigns",
        {
            "id": DATA_CAMPAIGN_ID, 
            "static_campaign_id": 1,
            "tutorial_id": TUTORIAL_ID, 
            "campaign_type": "SEGMENTED_MAB",
            "duration": 1,
            "segment_mix_id": 1,
            "start_time": datetime.now() + timedelta(weeks=1)
        },
        db=session,
    )
    
    # --- Insert Segment-Variant Performance Modifiers ---
    # Goal: Segment 1 (Mobile) favors V1. Segment 2 (Other) favors V2. (Reversal)

    # 1. Segment 1 (Mobile) - Variant 1 (Base 0.1) gets a positive modifier -> True CTR = 0.20 (WINNER)
    insert("segment_variant_performance", {
        "data_campaign_id": DATA_CAMPAIGN_ID, 
        "segment_id": SEGMENT_ID_MOBILE,
        "variant_id": VARIANT_ID_V1, # CORRECTED TO V1
        "performance_modifier": 0.10 # Base 0.1 + 0.10 = 0.20
    }, db=session)

    # 2. Segment 1 (Mobile) - Variant 2 (Base 0.2) gets a negative modifier -> True CTR = 0.15
    insert("segment_variant_performance", {
        "data_campaign_id": DATA_CAMPAIGN_ID, 
        "segment_id": SEGMENT_ID_MOBILE,
        "variant_id": VARIANT_ID_V2, # CORRECTED TO V2
        "performance_modifier": -0.05 # Base 0.2 - 0.05 = 0.15
    }, db=session)
    
    # 3. Segment 2 (Other) - Variant 1 (Base 0.1) gets a negative modifier -> True CTR = 0.05
    insert("segment_variant_performance", {
        "data_campaign_id": DATA_CAMPAIGN_ID, 
        "segment_id": SEGMENT_ID_OTHER,
        "variant_id": VARIANT_ID_V1, 
        "performance_modifier": -0.05 # Base 0.1 - 0.05 = 0.05
    }, db=session)

    # 4. Segment 2 (Other) - Variant 2 (Base 0.2) gets a positive modifier -> True CTR = 0.25 (WINNER)
    insert("segment_variant_performance", {
        "data_campaign_id": DATA_CAMPAIGN_ID, 
        "segment_id": SEGMENT_ID_OTHER,
        "variant_id": VARIANT_ID_V2, 
        "performance_modifier": 0.05 # Base 0.2 + 0.05 = 0.25
    }, db=session)

    # --- Print all tables to verify ---
    print_tables(None, db=session)

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python populate_test_segMAB.py --mode <dev|test>")
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
