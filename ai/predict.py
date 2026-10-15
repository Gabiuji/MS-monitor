from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd

from ms_monitor_ai.features import build_features


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Predict storage risk for one reading.")
    parser.add_argument("--model", type=Path, default=Path("ai/artifacts/risk_model.joblib"))
    parser.add_argument("--temperature", type=float, required=True, help="Ambient temperature in Celsius.")
    parser.add_argument("--humidity", type=float, required=True, help="Relative humidity in percent.")
    parser.add_argument("--grain-temperature", type=float, required=True)
    parser.add_argument("--days-in-storage", type=int, default=0)
    parser.add_argument("--hour", type=int, default=0)
    return parser.parse_args()


def predict(model_path: Path, temperature: float, humidity: float, grain_temperature: float,
            days_in_storage: int = 0, hour: int = 0) -> dict[str, object]:
    bundle = joblib.load(model_path)
    reading = pd.DataFrame(
        [
            {
                "lot_id": "inference",
                "ambient_temp_c": temperature,
                "ambient_rh_pct": humidity,
                "grain_temp_c": grain_temperature,
                "days_in_storage": days_in_storage,
                "hour_of_day": hour,
            }
        ]
    )
    features = build_features(reading)
    model = bundle["model"]
    probabilities = model.predict_proba(features)[0]
    classes = [str(value) for value in model.classes_]
    probability_by_class = dict(zip(classes, (round(float(value), 4) for value in probabilities)))
    risk_level = str(model.predict(features)[0])
    return {
        "risk_level": risk_level,
        "risk_score": round(float(max(probabilities)), 4),
        "probabilities": probability_by_class,
    }


def main() -> None:
    args = parse_args()
    result = predict(
        args.model,
        args.temperature,
        args.humidity,
        args.grain_temperature,
        args.days_in_storage,
        args.hour,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
