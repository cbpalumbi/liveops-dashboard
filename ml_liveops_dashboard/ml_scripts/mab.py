# Multi Armed Bandit
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List
import random, json
import numpy as np

from ml_liveops_dashboard.sqlite_models import DataCampaign, SegmentMix, SegmentMixEntry, Impression, Tutorial

def run_thompson_sampling(data_campaign_id: int, tutorial_id: int, db: Session):
    # Get static campaign id for this data campaign
    dc = db.query(DataCampaign).filter(DataCampaign.id == data_campaign_id).first()
    if not dc:
        raise ValueError("Data campaign not found")
    
    tutorial = db.query(Tutorial).options(selectinload(Tutorial.variants)).filter(Tutorial.id == dc.tutorial_id).first()
    if not tutorial:
        raise ValueError("Tutorial not found")

    static_tutorial_variants= tutorial.variants

    variant_scores = []

    zero_impression_variants = [
        v.json_id for v in static_tutorial_variants
        if db.query(func.count(Impression.id)).filter(
            Impression.data_campaign_id == data_campaign_id,
            Impression.tutorial_id == tutorial_id,
            Impression.variant_id == v.json_id
        ).scalar() == 0
    ]

    if zero_impression_variants:
        return random.choice(zero_impression_variants)

    for variant in static_tutorial_variants:
        clicks = db.query(func.sum(Impression.clicked)).filter(
            Impression.data_campaign_id == data_campaign_id,
            Impression.tutorial_id == tutorial_id,
            Impression.variant_id == variant.json_id
        ).scalar() or 0

        impressions = db.query(func.count(Impression.id)).filter(
            Impression.data_campaign_id == data_campaign_id,
            Impression.tutorial_id == tutorial_id,
            Impression.variant_id == variant.json_id
        ).scalar() or 0

        alpha = 1 + clicks
        beta = 1 + (impressions - clicks)
        score = random.betavariate(alpha, beta)
        variant_scores.append((variant.json_id, score))

    best_variant = max(variant_scores, key=lambda x: x[1])[0]
    return best_variant

# --- Serve Logic (can be used by API endpoint or local function) ---
def serve_variant(dc: DataCampaign, db: Session):
    tutorial = db.query(Tutorial).options(selectinload(Tutorial.variants)).filter(Tutorial.id == dc.tutorial_id).first()
    if not tutorial:
        raise ValueError("Tutorial not found")

    # Variant Selection Logic
    if dc.campaign_type.lower() == "mab":
        variant_id = run_thompson_sampling(dc.id, tutorial.id, db)
        chosen_variant = next(v for v in tutorial.variants if v.json_id == variant_id)
    else:
        chosen_variant = random.choice(tutorial.variants)

    return {
        "data_campaign_id": dc.id,
        "static_campaign_id": dc.static_campaign_id,
        "tutorial_id": tutorial.id,
        "variant": chosen_variant
    }

# --- Report Impression Core Logic (can be used by API endpoint or local function) ---
def report_impression(
    data_campaign_id: int,
    variant_id: int,
    clicked: bool,
    timestamp: datetime,
    db: Session,
    segment_id: int = None,
    player_context: Optional[str] = None # in json form
):
    """
    Store an impression in the database.
    If segment_id is provided, it will be recorded for segmented MAB campaigns.
    If player_context vector is provided, it will be stored as a JSON string. 
    """

    dc = db.query(DataCampaign).filter(DataCampaign.id == data_campaign_id).first()
    if not dc:
        raise ValueError("Data campaign not found")

    # Store impression in SQLite
    impression = Impression(
        data_campaign_id=data_campaign_id,
        tutorial_id=dc.tutorial_id,
        variant_id=variant_id,
        clicked=int(clicked),
        timestamp=timestamp,
        segment=segment_id,  # will be None for non-segmented campaigns
        player_context=player_context
    )
    db.add(impression)
    db.commit()

    if dc.campaign_type.lower() == "segmented_mab":
        # temporary unique logic for segmented mab to use the new thompson sampling class 
        if segment_id is None:
            raise ValueError("Segment ID required for segmented MAB campaigns")

        # Ensure segmented bandits are initialized
        if not segmented_bandits: # <-- should never happen
            init_segmented_bandits()

        # Lookup the correct segment’s bandit
        bandit = segmented_bandits.get(segment_id)
        if bandit is None:
            raise ValueError(f"No bandit found for segment {segment_id} in campaign {data_campaign_id}")

        # Update Thompson sampler with reward
        reward = 1 if clicked else 0
        bandit.update(variant_id, reward)
    elif dc.campaign_type.lower() == "contextual_mab":
        # temporary unique logic for contextual mab to use the lin ucb class
        global linucb_model

        # Convert the player context back to a vector
        context_vector = player_context_json_to_vector(player_context)

        # Update the model
        if linucb_model is not None:
            reward = 1 if clicked else 0
            linucb_model.update(variant_id - 1, reward, context_vector)
            #print(f"Updated LinUCB model for arm {variant_id} with reward {reward}")


    return {"status": "logged"}


import random

class ThompsonBandit:
    def __init__(self, variant_ids):
        # priors: start with Beta(1, 1) for each variant
        self.state = {
            vid: {"alpha": 1, "beta": 1}
            for vid in variant_ids
        }

    def select_variant(self):
        """Sample from each variant’s Beta and return the winner."""
        scores = {
            vid: random.betavariate(s["alpha"], s["beta"])
            for vid, s in self.state.items()
        }
        return max(scores, key=scores.get)

    def update(self, variant_id: int, clicked: bool):
        """Update counts after an impression result."""
        if clicked:
            self.state[variant_id]["alpha"] += 1
        else:
            self.state[variant_id]["beta"] += 1


def run_thompson_sampling_segmented(data_campaign_id: int, tutorial_id: int, segment_id: int, db: Session):
    """
    Run Thompson Sampling for a specific segment.
    """
    # Get static campaign id for this data campaign
    dc = db.query(DataCampaign).filter(DataCampaign.id == data_campaign_id).first()
    if not dc:
        raise ValueError("Data campaign not found")
    
    tutorial = db.query(Tutorial).options(selectinload(Tutorial.variants)).filter(Tutorial.id == dc.tutorial_id).first()
    if not tutorial:
        raise ValueError("Tutorial not found")

    static_tutorial_variants= tutorial.variants

    variant_scores = []

    # Find variants with zero impressions in this segment
    zero_impression_variants = [
        v.json_id for v in static_tutorial_variants
        if db.query(func.count(Impression.id)).filter(
            Impression.data_campaign_id == data_campaign_id,
            Impression.tutorial_id == tutorial_id,
            Impression.variant_id == v.json_id,
            Impression.segment == segment_id  # filter by segment
        ).scalar() == 0
    ]

    if zero_impression_variants:
        return random.choice(zero_impression_variants)

    # Calculate Thompson Sampling score per variant
    for variant in static_tutorial_variants:
        clicks = db.query(func.sum(Impression.clicked)).filter(
            Impression.data_campaign_id == data_campaign_id,
            Impression.tutorial_id == tutorial_id,
            Impression.variant_id == variant.json_id,
            Impression.segment == segment_id  # filter by segment
        ).scalar() or 0

        impressions = db.query(func.count(Impression.id)).filter(
            Impression.data_campaign_id == data_campaign_id,
            Impression.tutorial_id == tutorial_id,
            Impression.variant_id == variant.json_id,
            Impression.segment == segment_id  # filter by segment
        ).scalar() or 0

        alpha = 1 + clicks
        beta = 1 + (impressions - clicks)
        score = random.betavariate(alpha, beta)
        variant_scores.append((variant.json_id, score))

    # Return the variant with highest sampled score
    best_variant = max(variant_scores, key=lambda x: x[1])[0]
    return best_variant

# TODO: Needs to be stored per data campaign, not globally
segmented_bandits = {}
def init_segmented_bandits(segment_ids, variant_ids):
    for seg in segment_ids:
        segmented_bandits[seg] = ThompsonBandit(variant_ids)

def serve_variant_segmented(dc: DataCampaign, db: Session):
    """
    Serve a variant for a campaign using Segmented MAB.
    Randomly assigns the impression to a segment according to the segment_mix,
    then runs Thompson Sampling for that segment.
    Returns chosen variant and segment info.
    """
    # Load segment mix and entries
    segment_mix = db.query(SegmentMix).filter(
        SegmentMix.id == dc.segment_mix_id
    ).first()
    if not segment_mix:
        raise ValueError("Segment mix not found")

    entries = db.query(SegmentMixEntry).filter(
        SegmentMixEntry.segment_mix_id == segment_mix.id
    ).all()
    if not entries:
        raise ValueError("No entries found for segment mix")
    
    tutorial = db.query(Tutorial).options(selectinload(Tutorial.variants)).filter(Tutorial.id == dc.tutorial_id).first()
    if not tutorial:
        raise ValueError("Tutorial not found")

    static_tutorial_variants= tutorial.variants

    # Initialize bandits if needed
    if segmented_bandits == {}:
        segment_ids = [e.segment_id for e in entries]
        variant_ids = [v.json_id for v in static_tutorial_variants]
        init_segmented_bandits(segment_ids, variant_ids)

    # weighted random segment choice
    total_weight = sum(e.percentage for e in entries)
    rnd = random.uniform(0, total_weight)
    cumulative = 0
    selected_segment = entries[0].segment_id  # default fallback
    for entry in entries:
        cumulative += entry.percentage
        if rnd <= cumulative:
            selected_segment = entry.segment_id
            break

    # Retrieve this segment's bandit and run Thompson sampling
    bandit = segmented_bandits[selected_segment]
    variant_id = bandit.select_variant()

    # Get static campaign info for variant details TODO: cache this at startup
    with open("ml_liveops_dashboard/src/data/campaigns.json", "r", encoding="utf-8") as f:
        static_campaigns = json.load(f)
    static_campaign = next((c for c in static_campaigns if c["id"] == dc.static_campaign_id), None)
    if not static_campaign:
        raise ValueError("Static campaign not found")

    tutorial = next((b for b in static_campaign["tutorials"] if b["id"] == dc.tutorial_id), None)
    if not tutorial:
        raise ValueError("Tutorial not found in static campaign")

    chosen_variant = next(v for v in tutorial["variants"] if v["id"] == variant_id)

    return {
        "data_campaign_id": dc.id,
        "static_campaign_id": dc.static_campaign_id,
        "tutorial_id": dc.tutorial_id,
        "segment_id": selected_segment,
        "variant": chosen_variant
    }

def player_context_json_to_vector(ctx_json: str) -> List[float]:
    ctx = json.loads(ctx_json)

    # exclude region and device type because they are not numeric. could add back later but need to convert to enum or something
    vector = [
        ctx["age"],
        ctx["sessions_per_day"],
        ctx["avg_session_length"],
        ctx["lifetime_spend"],
    ] + ctx["playstyle_vector"]

    return vector

class LinUCB: 
    def __init__(self, n_arms, n_features, alpha=0.05): # alpha controls prioritization of exploration vs exploitation
        self.n_arms = n_arms
        self.n_features = n_features
        self.alpha = alpha
        self.A = [np.identity(n_features) for _ in range(n_arms)]  # A_i: DxD matrix for each arm
        self.b = [np.zeros(n_features) for _ in range(n_arms)]  # b_i: Dx1 vector for each arm

    def choose_arm(self, context_vector):
        np_context_vector = np.array(context_vector)
        p_t = np.zeros(self.n_arms)
        for i in range(self.n_arms):
            A_i_inv = np.linalg.inv(self.A[i])
            theta_i = np.dot(A_i_inv, self.b[i])
            
            # The LinUCB formula: E[r] + exploration term
            # E[r] = theta_i^T * x
            # exploration = alpha * sqrt(x^T * A_i_inv * x)
            p_t[i] = np.dot(theta_i.T, np_context_vector) + self.alpha * np.sqrt(np.dot(np_context_vector.T, np.dot(A_i_inv, np_context_vector)))
        
        return np.argmax(p_t)

    def update(self, chosen_arm, reward, context_vector):
        np_context_vector = np.array(context_vector)
        self.A[chosen_arm] += np.outer(np_context_vector, np_context_vector)
        self.b[chosen_arm] += reward * np_context_vector

linucb_model = None #TODO: persist

def serve_variant_contextual(dc: DataCampaign, db: Session, player_context: Optional[str] = None):
    """
    Serve a variant for a campaign using LinUCB.
    """
    global linucb_model

    tutorial = db.query(Tutorial).options(selectinload(Tutorial.variants)).filter(Tutorial.id == dc.tutorial_id).first()
    if not tutorial:
        raise ValueError("Tutorial not found")

    static_tutorial_variants= tutorial.variants

    tutorial_variant_ids = [v.json_id for v in static_tutorial_variants]

    player_vector = player_context_json_to_vector(player_context)
    n_arms = len(tutorial_variant_ids)
    n_features = len(player_vector)

    # Initialize the model on the first call
    if linucb_model is None:
        linucb_model = LinUCB(n_arms, n_features)

    # Choose the best variant based on the context vector
    chosen_arm_index = linucb_model.choose_arm(player_vector)
    chosen_variant = tutorial_variant_ids[chosen_arm_index]
    
    return {
        "data_campaign_id": dc.id,
        "static_campaign_id": dc.static_campaign_id,
        "tutorial_id": dc.tutorial_id,
        "variant": chosen_variant
    }

     

