# populate_tutorials.py
# Populates the db with the tutorials defined in static_tutorials.json
import sys
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ml_liveops_dashboard.sqlite_models import Base, Tutorial, Variant
from ml_liveops_dashboard.db_utils import clear
from constants import DB_PATH, TESTS_DB_PATH

def populate(db_path):
    """Populates the database with the tutorials and variants defined in static_tutorials.json"""
    
    # --- SQLAlchemy Engine and Session Setup ---
    engine = create_engine(db_path, echo=False)  
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # --- Create all tables from Base ---
    Base.metadata.create_all(engine)

    with open("ml_liveops_dashboard/data/static_tutorials.json", "r", encoding="utf-8") as f:
        CAMPAIGN_DATA = json.load(f)

    print("\n--- POPULATE TUTORIALS: Inserting Tutorial and Variant Definitions ---")

    # --- Clear existing tables ---
    clear("tutorials", db=session)
    clear("variants", db=session)

    if not CAMPAIGN_DATA:
        print("Error: CAMPAIGN_DATA is empty.")
        return

    # ignoring top level grouping because of legacy setup.
    # TODO: fix 
    tutorial_definitions = CAMPAIGN_DATA[0].get("tutorials", [])
    
    for tutorial_data in tutorial_definitions:
        # Create the parent Tutorial object
        tutorial_obj = Tutorial(
            id=tutorial_data["id"],
            title=tutorial_data["title"]
        )

        # Loop through the variants and append them to the tutorial object
        # They can't all have the same base CTRs or regret will be 0 for any kind of campaign
        for variant_data in tutorial_data.get("variants", []):
            variant_obj = Variant(
                # db_id will be auto-incremented, we only set the fixed data
                json_id=variant_data["id"],
                name=variant_data["name"],
                color=variant_data["color"],
                base_ctr=variant_data["base_ctr"],
            )
            tutorial_obj.variants.append(variant_obj)
        
        # Add the parent object. All related variants will be inserted too.
        session.add(tutorial_obj)
        print(f"Added Tutorial: {tutorial_obj.title} with {len(tutorial_obj.variants)} variants.")

    session.commit()
    
if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python populate_tutorials.py --mode <dev|test>")
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
