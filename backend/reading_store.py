import csv
import io
import json
import os
import shutil
import tempfile
import time
from collections import deque
from pathlib import Path
from threading import Lock


HISTORY_CAPACITY = 3600
LEGACY_CSV_FIELDS = (
    "received_at", "device_id", "uptime_ms", "window_ms", "temperature_c",
    "humidity_pct", "dht_ok", "probe_temperature_c", "probe_ok",
    "vibration_do", "vibration_transitions",
)
AI_CSV_FIELDS = ("ai_source", "ai_model_version", "ai_risk_level", "ai_risk_score", "ai_confidence", "ai_inference_us")
CSV_FIELDS = LEGACY_CSV_FIELDS + AI_CSV_FIELDS
AI_FIELDS = ("source", "model_version", "risk_level", "risk_score", "confidence", "inference_us")


def inflate_row(row):
    reading = {key: row[key] if key in {"device_id", "received_at"}
               else json.loads(row[key]) if row[key] else None for key in LEGACY_CSV_FIELDS}
    reading["embedded_diagnosis"] = None
    if row.get("ai_source"):
        reading["embedded_diagnosis"] = {
            key: row[column] if key in {"source", "model_version", "risk_level"}
            else json.loads(row[column]) if row[column] else None
            for key, column in zip(AI_FIELDS, AI_CSV_FIELDS)
        }
    return reading


class CsvReadingStore:
    def __init__(self, path: Path):
        self.path = path
        self._lock = Lock()
        self._history = deque(maxlen=HISTORY_CAPACITY)
        self._legacy = False
        if path.is_file() and path.stat().st_size:
            with path.open(encoding="utf-8", newline="") as source:
                reader = csv.DictReader(source)
                if reader.fieldnames not in (list(CSV_FIELDS), list(LEGACY_CSV_FIELDS)):
                    raise ValueError(f"Unexpected reading CSV columns: {path}")
                self._legacy = reader.fieldnames == list(LEGACY_CSV_FIELDS)
                for row in reader:
                    self._history.append(inflate_row(row))

    def _migrate_legacy(self):
        # Keep the original collection before atomically extending its columns.
        backup = self.path.with_name(f"{self.path.stem}.before-embedded-{time.time_ns()}.csv")
        with self.path.open("rb") as source, backup.open("xb") as destination:
            shutil.copyfileobj(source, destination)
            destination.flush()
            os.fsync(destination.fileno())
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", delete=False,
                                             dir=self.path.parent, suffix=".csv.tmp") as destination:
                temporary = Path(destination.name)
                writer = csv.DictWriter(destination, fieldnames=CSV_FIELDS)
                writer.writeheader()
                with self.path.open(encoding="utf-8", newline="") as source:
                    writer.writerows(csv.DictReader(source))
                destination.flush()
                os.fsync(destination.fileno())
            os.replace(temporary, self.path)
            self._legacy = False
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()

    def append(self, reading: dict):
        diagnosis = reading.get("embedded_diagnosis") or {}
        flattened = {key: reading.get(key) for key in LEGACY_CSV_FIELDS}
        flattened.update({column: diagnosis.get(key) for key, column in zip(AI_FIELDS, AI_CSV_FIELDS)})
        row = {key: value if isinstance(value, str) else json.dumps(value) if value is not None else ""
               for key, value in flattened.items()}
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self._legacy:
                self._migrate_legacy()
            with self.path.open("ab", buffering=0) as destination:
                original_size = destination.tell()
                buffer = io.StringIO(newline="")
                writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS)
                if original_size == 0:
                    writer.writeheader()
                writer.writerow(row)
                content = buffer.getvalue().encode("utf-8")
                try:
                    if destination.write(content) != len(content):
                        raise OSError("Incomplete CSV write")
                    os.fsync(destination.fileno())
                except OSError:
                    # Roll back this append so a failed write cannot leave a partial row.
                    try:
                        os.ftruncate(destination.fileno(), original_size)
                    except OSError:
                        pass
                    raise
            self._history.append(reading | {"embedded_diagnosis": reading.get("embedded_diagnosis")})

    def history(self, limit: int):
        with self._lock:
            return list(self._history)[-limit:]

    def export(self):
        # Snapshot the length while writes are locked; later appends are excluded.
        with self._lock:
            if not self.path.is_file():
                header = io.StringIO(newline="")
                csv.writer(header).writerow(CSV_FIELDS)
                return iter([header.getvalue().encode("utf-8")])
            source = self.path.open("rb")
            remaining = os.fstat(source.fileno()).st_size

        def chunks():
            nonlocal remaining
            with source:
                while remaining > 0:
                    chunk = source.read(min(65536, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        return chunks()
