# populate_mab_db.py
# Makes a MAB campaign 
from db_utils import insert, clear, print as print_tables

# --- Insert a regular MAB campaign ---
# No segments needed, so we skip seg-mix, seg, seg-mix-entry, seg-mab

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
