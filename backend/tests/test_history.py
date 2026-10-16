import csv
import io
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app import create_app
from reading_store import CSV_FIELDS, LEGACY_CSV_FIELDS, HISTORY_CAPACITY, CsvReadingStore


def reading(index=0):
    return dict(device_id="simulated-history-test", uptime_ms=index * 2500, window_ms=2500,
                temperature_c=24.8, humidity_pct=59.2, dht_ok=True,
                probe_temperature_c=25.25, probe_ok=True,
                vibration_do=0, vibration_transitions=index)


@pytest.fixture
def storage_path(tmp_path):
    return tmp_path / "collected" / "readings.csv"


def test_history_order_limit_and_full_csv(storage_path):
    with TestClient(create_app(csv_path=storage_path)) as client:
        assert client.get("/api/readings").json() == {"data": []}
        for index in range(5):
            assert client.post("/api/readings", json=reading(index)).status_code == 201
        history = client.get("/api/readings?limit=3").json()["data"]
        assert [row["uptime_ms"] for row in history] == [5000, 7500, 10000]
        assert history[-1] == client.get("/api/readings/latest").json()["data"]
        response = client.get("/api/readings/export")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert "attachment" in response.headers["content-disposition"]
        exported = list(csv.DictReader(io.StringIO(response.text)))
        assert len(exported) == 5
        assert exported[-1]["received_at"].endswith("Z")
        assert exported[-1]["probe_ok"] == "true"
        assert float(exported[-1]["probe_temperature_c"]) == 25.25
        assert response.content == storage_path.read_bytes()


def test_history_survives_restart_and_appends_without_duplicate_header(storage_path):
    with TestClient(create_app(csv_path=storage_path)) as client:
        original = client.post("/api/readings", json=reading()).json()
    with TestClient(create_app(csv_path=storage_path)) as client:
        assert client.get("/api/readings").json()["data"] == [original]
        # Connectivity still requires a POST accepted by this server instance.
        assert client.get("/api/readings/latest").json()["device_status"] == "waiting"
        client.post("/api/readings", json=reading(1))
        assert len(client.get("/api/readings").json()["data"]) == 2
    assert storage_path.read_text().count(",".join(CSV_FIELDS)) == 1


def test_failed_and_absent_sensors_roundtrip(storage_path):
    with TestClient(create_app(csv_path=storage_path)) as client:
        failed = reading() | dict(dht_ok=False, temperature_c=None, humidity_pct=None,
                                  probe_ok=False, probe_temperature_c=None)
        client.post("/api/readings", json=failed)
        legacy = reading()
        del legacy["probe_ok"]
        del legacy["probe_temperature_c"]
        client.post("/api/readings", json=legacy)
        rows = list(csv.DictReader(io.StringIO(client.get("/api/readings/export").text)))
        assert rows[0]["temperature_c"] == ""
        assert rows[0]["probe_ok"] == "false"
        assert rows[1]["probe_ok"] == ""
    with TestClient(create_app(csv_path=storage_path)) as client:
        rows = client.get("/api/readings").json()["data"]
        assert rows[0]["probe_ok"] is False
        assert rows[0]["temperature_c"] is None
        assert rows[1]["probe_ok"] is None
        assert rows[1]["probe_temperature_c"] is None


def test_invalid_post_is_not_recorded(storage_path):
    with TestClient(create_app(csv_path=storage_path)) as client:
        assert client.post("/api/readings", json=reading() | dict(window_ms=0)).status_code == 422
        assert client.get("/api/readings").json()["data"] == []
        assert client.get("/api/readings/export").text.strip() == ",".join(CSV_FIELDS)
        assert not storage_path.exists()


@pytest.mark.parametrize("limit", [0, -1, HISTORY_CAPACITY + 1, "abc", "1.5"])
def test_history_rejects_invalid_limits(storage_path, limit):
    with TestClient(create_app(csv_path=storage_path)) as client:
        assert client.get(f"/api/readings?limit={limit}").status_code == 422


def test_storage_failure_does_not_accept_or_replace_reading(storage_path, monkeypatch):
    with TestClient(create_app(csv_path=storage_path)) as client:
        accepted = client.post("/api/readings", json=reading()).json()

        def fail(*_args):
            raise OSError("Simulated disk full")

        monkeypatch.setattr(CsvReadingStore, "append", fail)
        response = client.post("/api/readings", json=reading(1))
        assert response.status_code == 503
        assert client.get("/api/readings/latest").json()["data"] == accepted
        assert client.get("/api/readings").json()["data"] == [accepted]


def test_history_memory_is_bounded_but_csv_keeps_all_records(storage_path, monkeypatch):
    import reading_store
    monkeypatch.setattr(reading_store, "HISTORY_CAPACITY", 3)
    store = CsvReadingStore(storage_path)
    for index in range(5):
        store.append(reading(index) | dict(received_at=datetime.now(timezone.utc).isoformat()))
    assert [row["uptime_ms"] for row in store.history(10)] == [5000, 7500, 10000]
    assert len(list(csv.DictReader(io.StringIO(b"".join(store.export()).decode())))) == 5
    restored = CsvReadingStore(storage_path)
    assert len(restored.history(10)) == 3


def test_failed_disk_sync_rolls_back_csv_append(storage_path, monkeypatch):
    with TestClient(create_app(csv_path=storage_path)) as client:
        client.post("/api/readings", json=reading())
        original = storage_path.read_bytes()

        def fail(_descriptor):
            raise OSError("Simulated disk sync failure")

        with monkeypatch.context() as patch:
            patch.setattr("reading_store.os.fsync", fail)
            assert client.post("/api/readings", json=reading(1)).status_code == 503
        assert storage_path.read_bytes() == original
        assert client.post("/api/readings", json=reading(2)).status_code == 201
        assert len(list(csv.DictReader(io.StringIO(client.get("/api/readings/export").text)))) == 2


def test_csv_snapshot_excludes_later_appends(storage_path):
    store = CsvReadingStore(storage_path)
    store.append(reading() | dict(received_at=datetime.now(timezone.utc).isoformat()))
    snapshot = store.export()
    store.append(reading(1) | dict(received_at=datetime.now(timezone.utc).isoformat()))
    assert len(list(csv.DictReader(io.StringIO(b"".join(snapshot).decode())))) == 1


def test_concurrent_posts_create_complete_rows(storage_path):
    with TestClient(create_app(csv_path=storage_path)) as client:
        with ThreadPoolExecutor(max_workers=4) as pool:
            codes = list(pool.map(lambda index: client.post("/api/readings", json=reading(index)).status_code, range(12)))
        assert codes == [201] * 12
        rows = list(csv.DictReader(io.StringIO(client.get("/api/readings/export").text)))
        assert len(rows) == 12
        assert {int(row["uptime_ms"]) for row in rows} == {index * 2500 for index in range(12)}


def test_embedded_diagnosis_survives_csv_and_restart(storage_path):
    diagnosis = dict(source="esp32", model_version="embedded-test", risk_level="moderate",
                     risk_score=0.4, confidence=0.8, inference_us=125)
    with TestClient(create_app(csv_path=storage_path)) as client:
        accepted = client.post("/api/readings", json=reading() | dict(embedded_diagnosis=diagnosis)).json()
        assert accepted["embedded_diagnosis"] == diagnosis
        csv_data = list(csv.DictReader(io.StringIO(client.get("/api/readings/export").text)))[0]
        assert csv_data["ai_source"] == "esp32"
        assert csv_data["ai_model_version"] == "embedded-test"
        assert csv_data["ai_risk_level"] == "moderate"
    with TestClient(create_app(csv_path=storage_path)) as client:
        assert client.get("/api/readings").json()["data"] == [accepted]


def test_existing_csv_is_migrated_with_original_backup(storage_path):
    storage_path.parent.mkdir(parents=True)
    original_row = reading() | dict(received_at="2026-10-15T12:00:00Z")
    with storage_path.open("w", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=LEGACY_CSV_FIELDS)
        writer.writeheader()
        writer.writerow({key: value if isinstance(value, str) else json.dumps(value)
                         for key, value in original_row.items()})
    original = storage_path.read_bytes()
    with TestClient(create_app(csv_path=storage_path)) as client:
        assert client.get("/api/readings").json()["data"][0]["embedded_diagnosis"] is None
        assert client.post("/api/readings", json=reading(1)).status_code == 201
        rows = list(csv.DictReader(io.StringIO(client.get("/api/readings/export").text)))
        assert len(rows) == 2
        assert rows[0]["received_at"] == original_row["received_at"]
        assert rows[0]["ai_source"] == ""
    backups = list(storage_path.parent.glob("readings.before-embedded-*.csv"))
    assert len(backups) == 1
    assert backups[0].read_bytes() == original
