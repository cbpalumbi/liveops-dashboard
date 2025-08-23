from ml_liveops_dashboard import run_simulation
import pytest

class FakeResponse:
    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data
        self.text = text
    def json(self): return self._json

@pytest.fixture
def mock_requests(monkeypatch):
    def fake_get(url, *_, **__):
        if "data_campaign" in url:
            return FakeResponse(200, {
                "id": 1,
                "static_campaign_id": 100,
                "campaign_type": "mab",
                "banner_id": 10
            })
        return FakeResponse(404, text="Not found")
    def fake_post(url, json=None, *_, **__):
        if "serve" in url:
            return FakeResponse(200, {"variant": {"id": 1, "name": "A"}, "segment_id": None})
        elif "report" in url:
            return FakeResponse(200, {})
        return FakeResponse(400, text="Bad request")

    monkeypatch.setattr(run_simulation, "requests", type("R", (), {
        "get": staticmethod(fake_get),
        "post": staticmethod(fake_post)
    }))
    return

def test_simulate_data_campaign_api(mock_requests, monkeypatch):
    monkeypatch.setattr(run_simulation, "load_static_campaigns", lambda: [{
        "id": 100,
        "banners": [{"id": 10, "variants": [{"id": 1, "name": "A"}]}]
    }])
    monkeypatch.setattr(run_simulation, "clear", lambda *_, **__: None)
    run_simulation.simulate_data_campaign(1, "api", impressions=3, delay=0)

def test_simulate_data_campaign_local(monkeypatch):
    monkeypatch.setattr(run_simulation, "requests", type("R", (), {
        "get": staticmethod(lambda url, *_, **__: FakeResponse(200, {
            "id": 1,
            "static_campaign_id": 100,
            "campaign_type": "mab",
            "banner_id": 10
        })),
        "post": staticmethod(lambda *_, **__: FakeResponse(200, {}))
    }))
    monkeypatch.setattr(run_simulation, "load_static_campaigns", lambda: [{
        "id": 100,
        "banners": [{"id": 10, "variants": [{"id": 1, "name": "A"}]}]
    }])
    monkeypatch.setattr(run_simulation, "clear", lambda *_, **__: None)
    monkeypatch.setattr(run_simulation, "run_mab_local", lambda *_, **__: None)
    run_simulation.simulate_data_campaign(1, "local", impressions=2, delay=0)

def test_simulate_data_campaign_segmented_api(monkeypatch):
    monkeypatch.setattr(run_simulation, "requests", type("R", (), {
        "get": staticmethod(lambda url, *_, **__: FakeResponse(200, {
            "id": 2,
            "static_campaign_id": 101,
            "campaign_type": "segmented_mab",
            "banner_id": 11
        })),
        "post": staticmethod(lambda url, json=None, *_, **__: (
            FakeResponse(200, {"variant": {"id": 2, "name": "B"}, "segment_id": "seg1"})
            if "serve" in url else FakeResponse(200, {})
        ))
    }))
    monkeypatch.setattr(run_simulation, "load_static_campaigns", lambda: [{
        "id": 101,
        "banners": [{"id": 11, "variants": [{"id": 2, "name": "B"}]}]
    }])
    monkeypatch.setattr(run_simulation, "clear", lambda *_, **__: None)
    monkeypatch.setattr(run_simulation, "generate_regret_summary", lambda *_, **__: None)
    monkeypatch.setattr(run_simulation, "get_ctr_for_variant", lambda *_: 0.5)
    run_simulation.simulate_data_campaign(2, "api", impressions=2, delay=0)

def test_simulate_data_campaign_segmented_local(monkeypatch):
    monkeypatch.setattr(run_simulation, "requests", type("R", (), {
        "get": staticmethod(lambda url, *_, **__: FakeResponse(200, {
            "id": 3,
            "static_campaign_id": 102,
            "campaign_type": "segmented_mab",
            "banner_id": 12
        })),
        "post": staticmethod(lambda *_, **__: FakeResponse(200, {}))
    }))
    monkeypatch.setattr(run_simulation, "load_static_campaigns", lambda: [{
        "id": 102,
        "banners": [{"id": 12, "variants": [{"id": 3, "name": "C"}]}]
    }])
    monkeypatch.setattr(run_simulation, "clear", lambda *_, **__: None)
    monkeypatch.setattr(run_simulation, "run_segmented_mab_local", lambda *_, **__: None)
    run_simulation.simulate_data_campaign(3, "local", impressions=1, delay=0)

def test_get_static_campaign_found():
    static_campaigns = [{"id": 1}, {"id": 2}]
    data_campaign = {"static_campaign_id": 2}
    result = run_simulation.get_static_campaign(data_campaign, static_campaigns)
    assert result == {"id": 2}

def test_get_static_campaign_not_found():
    static_campaigns = [{"id": 1}]
    data_campaign = {"static_campaign_id": 2}
    result = run_simulation.get_static_campaign(data_campaign, static_campaigns)
    assert result is None

