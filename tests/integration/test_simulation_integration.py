from ml_liveops_dashboard.sqlite_models import DataCampaign

from ml_liveops_dashboard.run_simulation import simulate_data_campaign
from ml_liveops_dashboard.simulation_utils import SimulationResult
from ml_liveops_dashboard.sqlite_models import DataCampaign, SegmentMixEntry, Segment
from ml_liveops_dashboard.populate_db_scripts.populate_db import populate as populate_db 
from ml_liveops_dashboard.populate_db_scripts.populate_db2 import populate as populate_db2
from constants import TESTS_DB_PATH

def test_mab_simulation_flow():
    
    populate_db2(TESTS_DB_PATH)

    result = simulate_data_campaign(1, mode="local", impressions=100, db_path=TESTS_DB_PATH)
    assert isinstance(result, SimulationResult)
    assert result.cumulative_regret_mab < 2 * result.cumulative_regret_uniform, \
        "MAB regret should no more than half of uniform random regret"
    assert len(result.impression_log) == 100
    assert set(result.variant_counts.keys()) == {1, 2, 3}

def test_segmented_mab_simulation_flow(test_db_session):
    session = test_db_session

    # populate DB
    populate_db(TESTS_DB_PATH)

    # fetch data campaign
    dc = session.query(DataCampaign).filter(DataCampaign.id == 1).first()
    assert dc is not None

    # get segments
    entries = session.query(SegmentMixEntry).filter(
        SegmentMixEntry.segment_mix_id == dc.segment_mix_id
    ).all()
    segments = [
        session.query(Segment).filter(Segment.id == e.segment_id).first()
        for e in entries
    ]

    # run simulation
    result = simulate_data_campaign(dc.id, mode="local", impressions=100, db_path=TESTS_DB_PATH)

    # assertions
    assert isinstance(result, SimulationResult)

    # from generate_regret:
    #per_segment_regret[segment_id] = {
    #            "mab_regret": seg_cum_regret_mab,
    #            "uniform_regret": seg_cum_regret_uniform,
    #            "impressions": len(logs),
    #            "variant_counts": dict(variant_counts),
    #        }

    for seg in segments:
        assert seg.id in result.per_segment_regret.keys()

        seg_result = result.per_segment_regret[seg.id]
        assert seg_result["mab_regret"] < seg_result["uniform_regret"]
        assert seg_result["impressions"] > 0

