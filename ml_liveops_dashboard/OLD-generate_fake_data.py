import requests
import random
import time
import json
from datetime import datetime, timedelta
import os

API_BASE_URL = "http://localhost:8000"
CAMPAIGNS_JSON_PATH = os.path.join("src", "data", "campaigns.json")

# default simulation (Winter Wonderland holiday banner)
DEFAULT_SIMULATION = {
    "campaign_id": 2,
    "banner_id": 1,
    "variants": [
        {"variant_id": 1, "true_ctr": 0.05},
        {"variant_id": 2, "true_ctr": 0.10},
        {"variant_id": 3, "true_ctr": 0.02},
    ],
}

# TODO: Replace with db
def load_campaigns():
    with open(CAMPAIGNS_JSON_PATH, "r", encoding="utf-8") as f:
        campaigns = json.load(f)
    return campaigns

def find_campaign(campaigns, campaign_index):
    if campaign_index < 0 or campaign_index >= len(campaigns):
        print(f"Invalid simulation index {campaign_index}. Valid range: 0 to {len(campaigns)-1}")
        return None
    return campaigns[campaign_index]

def find_banner(campaign, banner_id=None):
    if banner_id is None:
        # Default to first banner
        return campaign["banners"][0] if campaign["banners"] else None
    for banner in campaign["banners"]:
        if banner["id"] == banner_id:
            return banner
    print(f"Banner ID {banner_id} not found in campaign '{campaign['name']}'")
    return None

def build_variants(banner, ctr_overrides=None):
    variants = []
    for v in banner.get("variants", []):
        variant_id = v.get("id") or v.get("variant_id")
        true_ctr = ctr_overrides.get(variant_id, v.get("true_ctr", 0.05)) if ctr_overrides else v.get("true_ctr", 0.05)
        variants.append({"variant_id": variant_id, "true_ctr": true_ctr})
    return variants

def simulate_impression(variant):
    clicked = random.random() < variant["true_ctr"]
    return clicked

# simulates a user clicking on a banner
def send_event(event):
    url = f"{API_BASE_URL}/report-event"
    try:
        response = requests.post(url, json=event)
        if response.status_code == 200:
            print(f"Reported event: {event}")
        else:
            print(f"Failed to report event: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error sending event: {e}")

def run_simulation(
    simulation_index=None,
    banner_id=None,
    ctr_overrides=None,
    num_impressions=5,
    start_time=None,
    interval_seconds=60,
):
    if simulation_index is None and banner_id is None and ctr_overrides is None:
        # No params given - use default hardcoded simulation
        print("No parameters passed in, running default Winter Wonderland simulation.")
        campaign = {
            "id": DEFAULT_SIMULATION["campaign_id"],
            "name": "Winter Wonderland (default)",
            "banners": [
                {
                    "id": DEFAULT_SIMULATION["banner_id"],
                    "variants": DEFAULT_SIMULATION["variants"]
                }
            ],
        }
        banner = campaign["banners"][0]
        variants = build_variants(banner, ctr_overrides)
    else:
        # Use campaigns.json and params to find campaign/banner
        campaigns = load_campaigns()
        if simulation_index is None:
            print("Simulation index not provided; defaulting to 0")
            simulation_index = 0
        campaign = find_campaign(campaigns, simulation_index)
        if not campaign:
            return

        banner = find_banner(campaign, banner_id)
        if not banner:
            return

        variants = build_variants(banner, ctr_overrides)

    if not variants:
        print("No variants found in banner, exiting.")
        return

    current_time = start_time or datetime.now()

    for i in range(num_impressions):
        variant = random.choice(variants)
        clicked = simulate_impression(variant)
        event = {
            "campaign_id": campaign["id"],
            "banner_id": banner["id"],
            "variant_id": variant["variant_id"],
            "clicked": clicked,
            "timestamp": current_time.isoformat(),
        }
        send_event(event)
        current_time += timedelta(seconds=interval_seconds)
        time.sleep(0.1)  # remove or reduce for faster runs

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run a banner click simulation.")
    parser.add_argument("--campaign", type=int, help="Static campaign index override")
    parser.add_argument("--banner", type=int, help="Banner ID override")
    parser.add_argument(
        "--ctr",
        nargs="*",
        metavar="VARIANT_ID:CTR",
        help="Override true CTR per variant (e.g. 1:0.1 2:0.05)",
    )
    parser.add_argument("--impressions", type=int, default=5, help="Number of impressions to simulate")
    args = parser.parse_args()

    # Parse CTR overrides into a dict {variant_id: ctr}
    ctr_overrides = {}
    if args.ctr:
        for pair in args.ctr:
            try:
                vid, val = pair.split(":")
                ctr_overrides[int(vid)] = float(val)
            except Exception:
                print(f"Ignoring invalid CTR override '{pair}', expected format VARIANT_ID:CTR")
    else:
        ctr_overrides = None

    run_simulation(
        simulation_index=args.simulation,
        banner_id=args.banner,
        ctr_overrides=ctr_overrides,
        num_impressions=args.impressions,
    )
