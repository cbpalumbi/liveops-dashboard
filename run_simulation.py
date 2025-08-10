import requests
import time
from datetime import datetime, timedelta
import hashlib
import json
import random
from collections import Counter

from main import SessionLocal

from mab import serve_variant, report_impression

API_BASE = "http://localhost:8000" 

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

def print_regret_summary(impression_log, true_ctrs):
    best_ctr = max(true_ctrs.values())
    cumulative_regret_mab = 0.0
    cumulative_regret_uniform = 0.0
    total_impressions = len(impression_log)
    uniform_prob = 1 / len(true_ctrs)

    for i, impression in enumerate(impression_log, 1):
        variant_id = impression["variant_id"]

        # Regret is the difference between the click through rate we could'v ehad if we had served
        # the ideal banner variant, minus the CTR of the one we *did* serve
        mab_regret = best_ctr - true_ctrs[variant_id]
        cumulative_regret_mab += mab_regret

        # Uniform expected click is expected CTR averaged over variants
        expected_click_uniform = sum(ctr * uniform_prob for ctr in true_ctrs.values())
        cumulative_regret_uniform += best_ctr - expected_click_uniform

        if i % 10 == 0 or i == total_impressions:
            print(f"Impression {i}: Cumulative regret MAB = {cumulative_regret_mab:.3f}, Uniform = {cumulative_regret_uniform:.3f}")

    variant_ids = [entry["variant_id"] for entry in impression_log]
    counts = Counter(variant_ids)

    print("\nImpression counts per variant:")
    for variant_id, count in counts.items():
        print(f"Variant ID {variant_id}: {count} impressions")

    print(f"\nFinal cumulative regret after {total_impressions} impressions:")
    print(f"  MAB policy: {cumulative_regret_mab:.3f}")
    print(f"  Uniform random: {cumulative_regret_uniform:.3f}")

def simulate_data_campaign(data_campaign_id, mode, impressions=50, delay=0.02):
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

    impression_log = []

    # Hash once to find true CTRs for banner variants
    banner_id = data_campaign["banner_id"]
    static_banner_variants = [v["id"] for b in static_campaign["banners"] if b["id"] == banner_id for v in b["variants"]]
    true_ctrs = {
        variant_id: get_ctr_for_variant(static_campaign, banner_id, variant_id)
        for variant_id in static_banner_variants
    }

    if mode == "api":
        run_simulation_via_api(true_ctrs, impression_log, impressions, delay)
    elif mode == "local":
        run_simulation_local(true_ctrs, impression_log, impressions, delay)

def run_simulation_local(true_ctrs, impression_log, impressions, delay):
    current_time = datetime.utcnow()
    db = SessionLocal()
    try:
        for i in range(impressions):

            # Serve a variant
            serve_data = serve_variant(data_campaign_id, db)
            variant = serve_data["variant"]

            ctr = true_ctrs[variant["id"]]
           
            # Simulate click event with probability of success
            rand = random.random()
            clicked = rand < ctr
            #print("name ", variant["name"])
            #print("rand ", rand)
            #print("ctr ", ctr)

            report_impression(data_campaign_id, variant["id"], clicked, db)

            # Log impression for regret calculation (clicked as int 0/1)
            impression_log.append({
                "variant_id": variant["id"],
                "clicked": int(clicked)
            })

            print(f"Impression {i+1}: variant {variant['name']} (id {variant['id']}), clicked: {clicked} (CTR={ctr:.2%})")

            current_time += timedelta(minutes=1)
        

            time.sleep(delay)  # optional delay between impressions
    finally:
        db.close()

    # After all impressions, print regret summary
    print_regret_summary(impression_log, true_ctrs)


def run_simulation_via_api(true_ctrs, impression_log, impressions, delay):
    current_time = datetime.utcnow()
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
            "clicked": clicked
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
    print_regret_summary(impression_log, true_ctrs)

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print("Usage: python simulation.py --mode <api|local> <data_campaign_id> [impressions]")
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

