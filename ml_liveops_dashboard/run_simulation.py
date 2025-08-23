import requests
import time
from datetime import datetime, timedelta, timezone
import random

from ml_liveops_dashboard.local_simulation import run_mab_local, run_segmented_mab_local, run_contextual_mab_local
from ml_liveops_dashboard.simulation_utils import print_regret_summary, get_ctr_for_variant, load_static_campaigns
from ml_liveops_dashboard.db_utils import clear

API_BASE = "http://localhost:8000" 

def get_static_campaign(data_campaign, static_campaigns):
    return next((c for c in static_campaigns if c["id"] == data_campaign["static_campaign_id"]), None)


def simulate_data_campaign(data_campaign_id, mode, impressions=50, delay=0.02):
    # Get data campaign details
    r = requests.get(f"{API_BASE}/data_campaign/{data_campaign_id}")
    if r.status_code != 200:
        print("Data campaign not found:", r.text)
        return
    data_campaign = r.json()

    static_campaigns = load_static_campaigns()
    static_campaign = get_static_campaign(data_campaign, static_campaigns)
    if not static_campaign:
        print("Static campaign for data campaign not found")
        return
    
    # Clear any old impressions for this data campaign
    clear("imp",data_campaign["id"])

    # Branch by campaign type
    campaign_type = data_campaign["campaign_type"].lower()
    if campaign_type == "segmented_mab":
        if mode == "api":
            run_segmented_mab_via_api(data_campaign, static_campaign, impressions, delay)
        elif mode == "local":
            run_segmented_mab_local(data_campaign["id"], impressions, delay)
    elif campaign_type == "mab":
        # Original MAB / random campaign flow

        # Hash once to find true CTRs for banner variants
        banner_id = data_campaign["banner_id"]
        static_banner_variants = [
            v["id"] for b in static_campaign["banners"] if b["id"] == banner_id for v in b["variants"]
        ]
        true_ctrs = {
            variant_id: get_ctr_for_variant(static_campaign, banner_id, variant_id)
            for variant_id in static_banner_variants
        }

        if mode == "api":
            run_simulation_via_api(data_campaign["id"], true_ctrs, [], impressions, delay)
        elif mode == "local":
            run_mab_local(data_campaign["id"], impressions, delay)

    elif campaign_type == "contextual_mab":
        if mode == "api":
            run_contextual_mab_via_api(data_campaign["id"], impressions)
        elif mode == "local":
            run_contextual_mab_local(data_campaign["id"], impressions)
            
    else:
        print("No simulation running")

def run_contextual_mab_via_api(data_campaign_id: int, impressions: int):
    serve_resp = requests.post(
        f"{API_BASE}/serve",
        json={
            "data_campaign_id": data_campaign_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "player_context": {
                "player_id": 3,
                "age": 27,
                "region": "NA",
                "device_type": "Android",
                "sessions_per_day": 3,
                "avg_session_length": 13,
                "lifetime_spend": 2.83,
                "playstyle_vector": [0.622, 0.235, 0.143],
            },
        },
    )

    serve_resp = requests.post(
        f"{API_BASE}/serve",
        json={
            "data_campaign_id": data_campaign_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "player_context": {
                "player_id": 4,
                "age": 27,
                "region": "NA",
                "device_type": "Android",
                "sessions_per_day": 3,
                "avg_session_length": 13,
                "lifetime_spend": 2.83,
                "playstyle_vector": [0.622, 0.235, 0.143],
            },
        },
    )

    serve_resp = requests.post(
        f"{API_BASE}/serve",
        json={
            "data_campaign_id": data_campaign_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "player_context": {
                "player_id": 5,
                "age": 15,
                "region": "EU",
                "device_type": "Tablet",
                "sessions_per_day": 1,
                "avg_session_length": 31,
                "lifetime_spend": 8.01,
                "playstyle_vector": [0.122, 0.535, 0.643],
            },
        },
    )
    return

def run_segmented_mab_via_api(data_campaign, static_campaign, impressions, delay):
    impression_log = []

    # Compute true CTRs once for regret calculation
    banner_id = data_campaign["banner_id"]
    static_banner_variants = [
        v["id"] for b in static_campaign["banners"] if b["id"] == banner_id for v in b["variants"]
    ]
    true_ctrs = {
        variant_id: get_ctr_for_variant(static_campaign, banner_id, variant_id)
        for variant_id in static_banner_variants
    }

    for i in range(impressions):
        serve_resp = requests.post(f"{API_BASE}/serve", json={"data_campaign_id": data_campaign["id"]})
        if serve_resp.status_code != 200:
            print("Serve error:", serve_resp.text)
            break
        serve_data = serve_resp.json()
        variant = serve_data["variant"]
        segment_id = serve_data["segment_id"]

        ctr = true_ctrs[variant["id"]]
        clicked = random.random() < ctr

        report_payload = {
            "data_campaign_id": data_campaign["id"],
            "variant_id": variant["id"],
            "clicked": clicked,
            "segment_id": segment_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        report_resp = requests.post(f"{API_BASE}/report", json=report_payload)
        if report_resp.status_code != 200:
            print("Report error:", report_resp.text)
            break

        # Log impression for regret calculation
        impression_log.append({
            "variant_id": variant["id"],
            "clicked": int(clicked),
            "segment_id": segment_id
        })

        print(f"Impression {i+1}: variant {variant['name']} (id {variant['id']}), segment {segment_id}, clicked: {clicked} (CTR={ctr:.2%})")
        time.sleep(delay)

    # Print regret summary after all impressions
    print_regret_summary(impression_log, true_ctrs, "segmented_mab")


def run_simulation_via_api(data_campaign_id, true_ctrs, impression_log, impressions, delay):
    current_time = datetime.now(timezone.utc)
    for i in range(impressions):
        # Serve a variant
        serve_resp = requests.post(f"{API_BASE}/serve", json={"data_campaign_id": data_campaign_id})
        if serve_resp.status_code != 200:
            print("Serve error:", serve_resp.text)
            break
        serve_data = serve_resp.json()
        variant = serve_data["variant"]
 
        ctr = true_ctrs[variant["id"]]

        # Simulate click event with probability of success
        clicked = random.random() < ctr

        # Report event 
        report_payload = {
            "data_campaign_id": data_campaign_id,
            "variant_id": variant["id"],
            "clicked": clicked,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        report_resp = requests.post(f"{API_BASE}/report", json=report_payload)
        if report_resp.status_code != 200:
            print("Report error:", report_resp.text)
            break

        # Log impression for regret calculation (clicked as int 0/1)
        impression_log.append({
            "variant_id": variant["id"],
            "clicked": int(clicked)
        })

        print(f"Impression {i+1}: variant {variant['name']} (id {variant['id']}), clicked: {clicked} (CTR={ctr:.2%})")

        current_time += timedelta(minutes=1)

        time.sleep(delay)  # optional delay between impressions

    # After all impressions, print regret summary
    print_regret_summary(impression_log, true_ctrs, "mab")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print("Usage: python run_simulation.py --mode <api|local> <data_campaign_id> [impressions]")
        sys.exit(1)

    # Check mode flag
    if sys.argv[1] != "--mode":
        print("First argument must be --mode")
        sys.exit(1)

    mode = sys.argv[2].lower()
    if mode not in ("api", "local"):
        print("Mode must be either 'api' or 'local'")
        sys.exit(1)

    data_campaign_id = int(sys.argv[3])
    impressions = int(sys.argv[4]) if len(sys.argv) > 4 else 50

    simulate_data_campaign(data_campaign_id, mode, impressions)

