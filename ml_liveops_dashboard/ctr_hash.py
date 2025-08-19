# Generates true Click Through Rate (CTR) for a variant.
# Based on hash of the static campaign data, so will always be
    # the same for a given variant

import hashlib
import json
import random

def get_ctr_for_variant(static_campaign, banner_id, variant_id, min_ctr=0.03, max_ctr=0.3):
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

                    # hash with SHA256
                    h = hashlib.sha256(variant_str.encode()).hexdigest()
                    seed = int(h[:8], 16)  # use first 8 hex digits for seed
                    rng = random.Random(seed)

                    # Deterministic CTR between min and max
                    ctr = rng.uniform(min_ctr, max_ctr)
                    return ctr
    raise ValueError("Variant not found")