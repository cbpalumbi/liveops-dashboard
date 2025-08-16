# populate_db.py
from db_utils import insert, clear, print as print_tables

clear("seg-mix")
clear("seg")
clear("seg-mix-entry")
clear("seg-mab")
clear("camp")

# ---  Insert segment mix ---
insert("seg-mix", {"name": "Platform Mix"})

# ---  Insert segments ---
insert("seg", {"name": "Mobile Users", "description": "", "rules_json": ""})
insert("seg", {"name": "Other Users", "description": "", "rules_json": ""})

# ---  Insert segment mix entries ---
insert("seg-mix-entry", {"segment_mix_id": 1, "segment_id": 1, "percentage": 40})
insert("seg-mix-entry", {"segment_mix_id": 1, "segment_id": 2, "percentage": 60})

# --- Insert segmented MAB campaign ---
insert("seg-mab", {"segment_mix_id": 1})

# --- Insert data campaign ---
insert(
    "camp",
    {
        "static_campaign_id": 1,
        "banner_id": 1,
        "campaign_type": "SEGMENTED_MAB",
        "segmented_mab_id": 1,
    },
)

# --- Print all tables to verify ---
print_tables(None)

