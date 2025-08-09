import requests
import time
from datetime import datetime, timedelta
import hashlib
import json
import random

API_BASE = "http://localhost:8000"  # Change if your FastAPI runs elsewhere

def get_static_campaign(data_campaign, static_campaigns):
    return next((c for c in static_campaigns if c["id"] == data_campaign["static_campaign_id"]), None)

def get_ctr_for_variant(static_campaign, banner_id, variant_id, min_ctr=0.05, max_ctr=0.3):
    for banner in static_campaign["banners"]:
        if banner["id"] == banner_id:
            for variant in banner["variants"]:
                if variant["id"] == variant_id:
                    variant_str = json.dumps({
                        "campaign_id": static_campaign["id"],
                        "banner_id": banner_id,
                        "variant_id": variant_id,
                        "color": variant.get("color")
                    }, sort_keys=True)
                    h = hashlib.sha256(variant_str.encode()).hexdigest()
                    seed = int(h[:8], 16)
                    rng = random.Random(seed)
                    ctr = rng.uniform(min_ctr, max_ctr)
                    return ctr
    raise ValueError("Variant not found")

def load_static_campaigns():
    with open("src/data/campaigns.json", "r", encoding="utf-8") as f:
        return json.load(f)

def simulate_data_campaign(data_campaign_id, impressions=50, delay=0.05):
    static_campaigns = load_static_campaigns()

    # Get data campaign details
    r = requests.get(f"{API_BASE}/data_campaign/{data_campaign_id}")
    if r.status_code != 200:
        print("Data campaign not found:", r.text)
        return
    data_campaign = r.json()

    static_campaign = get_static_campaign(data_campaign, static_campaigns)
    if not static_campaign:
        print("Static campaign for data campaign not found")
        return

    current_time = datetime.utcnow()

    for i in range(impressions):
        # Serve a variant
        serve_resp = requests.post(f"{API_BASE}/serve", json={"data_campaign_id": data_campaign_id})
        if serve_resp.status_code != 200:
            print("Serve error:", serve_resp.text)
            break
        serve_data = serve_resp.json()
        variant = serve_data["variant"]

        # Get CTR for variant
        ctr = get_ctr_for_variant(static_campaign, serve_data["banner_id"], variant["id"])

        # Simulate click event
        clicked = random.random() < ctr

        # Report event 
        # TODO: pass along timestamp 
        report_payload = {
            "data_campaign_id": data_campaign_id,
            "variant_id": variant["id"],
            "clicked": clicked
        }
        report_resp = requests.post(f"{API_BASE}/report", json=report_payload)
        if report_resp.status_code != 200:
            print("Report error:", report_resp.text)
            break

        print(f"Impression {i+1}: variant {variant['name']} (id {variant['id']}), clicked: {clicked} (CTR={ctr:.2%})")

        # Increment time by 1 minute ( could be changed)
        current_time += timedelta(minutes=1)

        time.sleep(delay)  # optional delay between impressions

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python simulation.py <data_campaign_id> [impressions]")
        sys.exit(1)

    data_campaign_id = int(sys.argv[1])
    impressions = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    simulate_data_campaign(data_campaign_id, impressions)
