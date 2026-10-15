from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from pydantic import BaseModel, ConfigDict

from ms_monitor_ai.features import build_features


class Diagnosis(BaseModel):
    model_config = ConfigDict(strict=True)

    risk_level: str
    risk_score: float | None
    confidence: float | None
    message: str
    reasons: list[str]
    model_version: str | None
    generated_at: datetime


class ModelUnavailableError(RuntimeError):
    pass


class RiskModel:
    def __init__(self, model_path: Path, model_version: str = "baseline-1"):
        self.model_path = model_path
        self.model_version = model_version
        self._bundle: dict[str, Any] | None = None

    def _load(self) -> dict[str, Any]:
        if self._bundle is None:
            if not self.model_path.is_file():
                raise ModelUnavailableError(f"Model not found: {self.model_path}")
            self._bundle = joblib.load(self.model_path)
        return self._bundle

    def diagnose(self, reading: Any, generated_at: datetime) -> Diagnosis:
        if not reading.dht_ok or reading.temperature_c is None or reading.humidity_pct is None:
            return self._unavailable("Diagnóstico indisponível: falha no DHT22.", generated_at)
        if reading.probe_ok is not True or reading.probe_temperature_c is None:
            return self._unavailable("Diagnóstico indisponível: leitura da sonda não recebida.", generated_at)

        bundle = self._load()
        sample = pd.DataFrame(
            [
                {
                    "lot_id": reading.device_id,
                    "days_in_storage": 0,
                    "hour_of_day": generated_at.hour,
                    "ambient_temp_c": reading.temperature_c,
                    "ambient_rh_pct": reading.humidity_pct,
                    "grain_temp_c": reading.probe_temperature_c,
                }
            ]
        )
        features = build_features(sample)
        model = bundle["model"]
        probabilities = model.predict_proba(features)[0]
        classes = [str(value) for value in model.classes_]
        probability_by_class = dict(zip(classes, probabilities))
        risk_level = str(model.predict(features)[0])
        severity = {"low": 0.0, "moderate": 0.33, "high": 0.66, "critical": 1.0}
        risk_score = sum(severity.get(level, 0.0) * probability
                         for level, probability in probability_by_class.items())
        confidence = max(probabilities)

        return Diagnosis(
            risk_level=risk_level,
            risk_score=round(float(risk_score), 4),
            confidence=round(float(confidence), 4),
            message=self._message(risk_level),
            reasons=self._reasons(reading),
            model_version=self.model_version,
            generated_at=generated_at,
        )

    def _unavailable(self, message: str, generated_at: datetime) -> Diagnosis:
        return Diagnosis(
            risk_level="unavailable",
            risk_score=None,
            confidence=None,
            message=message,
            reasons=[],
            model_version=None,
            generated_at=generated_at,
        )

    @staticmethod
    def _message(risk_level: str) -> str:
        return {
            "low": "Condições sem sinais relevantes de deterioração.",
            "moderate": "Condições que exigem acompanhamento.",
            "high": "Condições favoráveis à deterioração.",
            "critical": "Condições que exigem ação imediata.",
        }.get(risk_level, "Classificação recebida do modelo.")

    @staticmethod
    def _reasons(reading: Any) -> list[str]:
        reasons = []
        delta = reading.probe_temperature_c - reading.temperature_c
        if reading.humidity_pct >= 70:
            reasons.append("Umidade relativa do ar elevada.")
        if delta >= 2:
            reasons.append("Temperatura dos grãos acima da temperatura ambiente.")
        if reading.probe_temperature_c >= 25:
            reasons.append("Temperatura dos grãos elevada.")
        if not reasons:
            reasons.append("Leituras dos sensores dentro das faixas observadas.")
        return reasons
