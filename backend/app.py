import os
import time
from datetime import datetime, timezone
from threading import Lock
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Reading(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", allow_inf_nan=False)
    device_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    uptime_ms: int = Field(ge=0)
    window_ms: int = Field(gt=0)
    temperature_c: float | None = Field(ge=-40, le=80)
    humidity_pct: float | None = Field(ge=0, le=100)
    dht_ok: bool
    vibration_do: int = Field(ge=0, le=1)
    vibration_transitions: int = Field(ge=0)
    probe_temperature_c: float | None = Field(default=None, ge=0, le=1024)
    probe_ok: bool | None = None

    @model_validator(mode="after")
    def consistent_dht(self):
        present = self.temperature_c is not None and self.humidity_pct is not None
        absent = self.temperature_c is None and self.humidity_pct is None
        if (self.dht_ok and not present) or (not self.dht_ok and not absent):
            raise ValueError("Valid DHT readings require both values; failed readings require both null")
        return self

    @model_validator(mode="after")
    def consistent_probe(self):
        provided = self.model_fields_set & {"probe_temperature_c", "probe_ok"}
        if not provided:
            return self
        if provided != {"probe_temperature_c", "probe_ok"}:
            raise ValueError("Both probe fields must be provided together")
        if self.probe_ok is None:
            raise ValueError("Probe status must be a boolean when provided")
        if self.probe_ok != (self.probe_temperature_c is not None):
            raise ValueError("Valid probe readings require a temperature; failed readings require null")
        return self


class StoredReading(Reading):
    received_at: datetime


def create_app(clock=time.monotonic):
    app = FastAPI(title="MS-Monitor")

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request, error):
        # Do not serialize input/ctx again: they may contain NaN, Infinity, or exceptions.
        details = [{key: item[key] for key in ("type", "loc", "msg")} for item in error.errors()]
        return JSONResponse(status_code=422, content={"detail": details})

    origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in origins.split(",") if x.strip()],
                       allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
    lock = Lock()
    latest = None
    accepted_at = None

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/api/readings", status_code=201, response_model=StoredReading)
    def post_reading(reading: Reading):
        nonlocal latest, accepted_at
        with lock:
            latest = StoredReading(**reading.model_dump(exclude_unset=True), received_at=datetime.now(timezone.utc))
            accepted_at = clock()
            return latest

    @app.get("/api/readings/latest")
    def get_latest():
        with lock:
            if latest is None:
                return dict(data=None, device_status="waiting", age_seconds=None)
            age = max(0.0, clock() - accepted_at)
            return dict(data=latest, device_status="stale" if age >= 10 else "online", age_seconds=age)

    return app


app = create_app()
