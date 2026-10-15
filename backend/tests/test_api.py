import json
import pytest
from fastapi.testclient import TestClient
from app import create_app


@pytest.fixture
def setup():
    now = [100.0]
    with TestClient(create_app(clock=lambda: now[0])) as client:
        yield client, now


def payload():
    return dict(device_id="simulated-test", uptime_ms=15000, window_ms=2500,
                temperature_c=24.8, humidity_pct=59.2, dht_ok=True,
                vibration_do=0, vibration_transitions=44)


def test_waiting_and_health(setup):
    client, _ = setup
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/api/readings/latest").json() == dict(data=None, device_status="waiting", age_seconds=None)


def test_post_online_stale_and_recovery(setup):
    client, now = setup
    result = client.post("/api/readings", json=payload())
    assert result.status_code == 201
    assert result.json()["received_at"].endswith("Z")
    assert client.get("/api/readings/latest").json()["device_status"] == "online"
    now[0] += 10
    stale = client.get("/api/readings/latest").json()
    assert stale["device_status"] == "stale"
    assert stale["data"]["vibration_transitions"] == 44
    assert client.get("/health").status_code == 200
    client.post("/api/readings", json=payload())
    assert client.get("/api/readings/latest").json()["device_status"] == "online"


def test_dht_failure(setup):
    client, _ = setup
    data = payload() | dict(dht_ok=False, temperature_c=None, humidity_pct=None)
    assert client.post("/api/readings", json=data).status_code == 201
    latest = client.get("/api/readings/latest").json()["data"]
    assert latest["temperature_c"] is None
    assert latest["vibration_transitions"] == 44


@pytest.mark.parametrize("changes", [dict(humidity_pct=101), dict(temperature_c=-41),
    dict(temperature_c=81), dict(vibration_do=2), dict(vibration_do=True),
    dict(vibration_transitions=-1), dict(vibration_transitions=1.5), dict(window_ms=0),
    dict(uptime_ms=-1), dict(dht_ok=False), dict(temperature_c=None),
    dict(dht_ok=False, temperature_c=None), dict(device_id=""), dict(humidity_pct="59")])
def test_invalid(setup, changes):
    client, _ = setup
    assert client.post("/api/readings", json=payload() | changes).status_code == 422
    assert client.get("/api/readings/latest").json()["device_status"] == "waiting"


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity"])
def test_nonfinite(setup, value):
    client, _ = setup
    body = json.dumps(payload()).replace("24.8", value)
    assert client.post("/api/readings", content=body, headers={"Content-Type": "application/json"}).status_code == 422


def test_invalid_does_not_replace_or_refresh(setup):
    client, now = setup
    client.post("/api/readings", json=payload())
    now[0] += 11
    assert client.post("/api/readings", json=payload() | dict(window_ms=0)).status_code == 422
    latest = client.get("/api/readings/latest").json()
    assert latest["device_status"] == "stale"
    assert latest["data"]["window_ms"] == 2500


def test_cors(setup):
    client, _ = setup
    allowed = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    blocked = client.get("/health", headers={"Origin": "http://example.com"})
    assert "access-control-allow-origin" not in blocked.headers


@pytest.mark.parametrize("probe_temperature", [0, 25.25, 1023.75])
def test_probe_reading_roundtrip(setup, probe_temperature):
    client, now = setup
    data = payload() | dict(probe_ok=True, probe_temperature_c=probe_temperature)
    response = client.post("/api/readings", json=data)
    assert response.status_code == 201
    stored = response.json()
    assert stored["temperature_c"] == 24.8
    assert stored["probe_temperature_c"] == probe_temperature
    assert stored["probe_ok"] is True
    latest = client.get("/api/readings/latest").json()
    assert latest["data"] == stored
    assert latest["device_status"] == "online"
    now[0] += 10
    stale = client.get("/api/readings/latest").json()
    assert stale["device_status"] == "stale"
    assert stale["data"] == stored


@pytest.mark.parametrize("dht_ok,probe_ok", [(True, False), (False, True), (False, False)])
def test_sensor_failures_are_independent(setup, dht_ok, probe_ok):
    client, _ = setup
    data = payload() | dict(dht_ok=dht_ok, temperature_c=24.8 if dht_ok else None,
                            humidity_pct=59.2 if dht_ok else None,
                            probe_ok=probe_ok, probe_temperature_c=25.25 if probe_ok else None)
    assert client.post("/api/readings", json=data).status_code == 201
    stored = client.get("/api/readings/latest").json()["data"]
    for key, value in data.items():
        assert stored[key] == value


def test_legacy_reading_clears_previous_probe(setup):
    client, _ = setup
    client.post("/api/readings", json=payload() | dict(probe_ok=True, probe_temperature_c=25.25))
    legacy = client.post("/api/readings", json=payload())
    assert legacy.status_code == 201
    for stored in (legacy.json(), client.get("/api/readings/latest").json()["data"]):
        assert stored["probe_temperature_c"] is None
        assert stored["probe_ok"] is None


@pytest.mark.parametrize("probe_fields", [
    dict(probe_ok=True, probe_temperature_c=None),
    dict(probe_ok=False, probe_temperature_c=25.25),
    dict(probe_ok=None, probe_temperature_c=None),
    dict(probe_ok=None, probe_temperature_c=25.25),
    dict(probe_ok=True), dict(probe_ok=False), dict(probe_temperature_c=25.25),
    dict(probe_temperature_c=None), dict(probe_ok=None),
    dict(probe_ok=True, probe_temperature_c=-0.25),
    dict(probe_ok=True, probe_temperature_c=1024.25),
    dict(probe_ok=1, probe_temperature_c=25.25),
    dict(probe_ok=True, probe_temperature_c="25.25"),
    dict(probe_ok=True, probe_temperature_c=True),
])
def test_invalid_probe_preserves_last_reading(setup, probe_fields):
    client, now = setup
    valid = client.post("/api/readings", json=payload()).json()
    now[0] += 10
    assert client.post("/api/readings", json=payload() | probe_fields).status_code == 422
    latest = client.get("/api/readings/latest").json()
    assert latest["data"] == valid
    assert latest["device_status"] == "stale"


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity"])
def test_nonfinite_probe(setup, value):
    client, _ = setup
    body = json.dumps(payload() | dict(probe_ok=True, probe_temperature_c=25.25)).replace("25.25", value)
    response = client.post("/api/readings", content=body, headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert client.get("/api/readings/latest").json()["data"] is None
