"""
import run_simulation
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
    # Monkeypatch load_static_campaigns to return fake campaign
    monkeypatch.setattr(run_simulation, "load_static_campaigns", lambda: [{
        "id": 100,
        "banners": [{"id": 10, "variants": [{"id": 1, "name": "A"}]}]
    }])

    # Monkeypatch clear to no-op
    monkeypatch.setattr(run_simulation, "clear", lambda *_, **__: None)

    run_simulation.simulate_data_campaign(1, "api", impressions=3, delay=0)
"""