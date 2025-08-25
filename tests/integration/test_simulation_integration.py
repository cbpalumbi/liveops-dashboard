from ml_liveops_dashboard.sqlite_models import DataCampaign

from ml_liveops_dashboard.run_simulation import simulate_data_campaign
from ml_liveops_dashboard.simulation_utils import SimulationResult
from ml_liveops_dashboard.sqlite_models import DataCampaign, SegmentedMABCampaign, SegmentMixEntry, Segment

def test_mab_simulation_flow():
    exec(open("ml_liveops_dashboard/populate_db_scripts/populate_db2.py").read())
    result = simulate_data_campaign(1, mode="local", impressions=100)
    assert isinstance(result, SimulationResult)
    assert result.cumulative_regret_mab < 2 * result.cumulative_regret_uniform, \
        "MAB regret should no more than half of uniform random regret"
    assert len(result.impression_log) == 100
    assert set(result.variant_counts.keys()) == {1, 2}

def test_segmented_mab_simulation_flow(test_db_session):
    session = test_db_session

    # populate DB
    exec(open("ml_liveops_dashboard/populate_db_scripts/populate_db.py").read())

    # fetch data campaign
    dc = session.query(DataCampaign).filter(DataCampaign.id == 1).first()
    assert dc is not None

    # get segments
    smab = session.query(SegmentedMABCampaign).filter(
        SegmentedMABCampaign.id == dc.segmented_mab_id
    ).first()
    entries = session.query(SegmentMixEntry).filter(
        SegmentMixEntry.segment_mix_id == smab.segment_mix_id
    ).all()
    segments = [
        session.query(Segment).filter(Segment.id == e.segment_id).first()
        for e in entries
    ]

    # run simulation
    result = simulate_data_campaign(dc.id, mode="local", impressions=100)

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

