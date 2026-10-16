from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Diagnosis(BaseModel):
    model_config = ConfigDict(strict=True)

    risk_level: str
    risk_score: float | None
    confidence: float | None
    message: str
    reasons: list[str]
    model_version: str | None
    generated_at: datetime
    source: Literal["esp32", "unavailable"]
    inference_us: int | None = None


class EmbeddedDiagnosis(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", allow_inf_nan=False)
    source: Literal["esp32"]
    model_version: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")
    risk_level: Literal["low", "moderate", "high", "critical", "unavailable"]
    risk_score: float | None = Field(ge=0, le=1)
    confidence: float | None = Field(ge=0, le=1)
    inference_us: int = Field(ge=0, le=4294967295)

    @model_validator(mode="after")
    def consistent_result(self):
        if self.risk_level == "unavailable":
            if self.risk_score is not None or self.confidence is not None:
                raise ValueError("Unavailable inference requires null score and confidence")
        elif self.risk_score is None or self.confidence is None:
            raise ValueError("Available inference requires score and confidence")
        return self


def received_diagnosis(reading, received_at: datetime) -> Diagnosis:
    result = reading.embedded_diagnosis
    if result is None:
        return Diagnosis(risk_level="unavailable", risk_score=None, confidence=None,
                         message="Aguardando diagnóstico embarcado da ESP32. Atualize o firmware.",
                         reasons=[], model_version=None, generated_at=received_at, source="unavailable")
    return Diagnosis(
        **result.model_dump(), generated_at=received_at,
        message={
            "low": "Condições sem sinais relevantes de deterioração.",
            "moderate": "Condições que exigem acompanhamento.",
            "high": "Condições favoráveis à deterioração.",
            "critical": "Condições que exigem ação imediata.",
        }.get(result.risk_level, "Diagnóstico embarcado indisponível: verifique os sensores."),
        reasons=["Classificação executada localmente na ESP32."] if result.risk_level != "unavailable" else [],
    )
