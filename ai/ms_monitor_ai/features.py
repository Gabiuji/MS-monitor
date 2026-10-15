from __future__ import annotations

import numpy as np
import pandas as pd

BASE_FEATURES = (
    "ambient_temp_c",
    "ambient_rh_pct",
    "grain_temp_c",
)

MODEL_FEATURES = (
    *BASE_FEATURES,
    "grain_air_delta_c",
    "days_in_storage",
    "hour_sin",
    "hour_cos",
    "ambient_temp_rolling_6",
    "ambient_rh_rolling_6",
    "grain_temp_rolling_6",
)

TARGET = "mold_mycotoxin_risk_level"


def build_features(rows: pd.DataFrame) -> pd.DataFrame:
    """Build model inputs using only values available during monitoring."""
    required = {*BASE_FEATURES, "days_in_storage", "hour_of_day", "lot_id"}
    missing = sorted(required - set(rows.columns))
    if missing:
        raise ValueError(f"Missing feature columns: {', '.join(missing)}")

    frame = rows.copy()
    frame["_input_order"] = np.arange(len(frame))
    frame = frame.sort_values(["lot_id", "days_in_storage", "hour_of_day", "_input_order"])

    frame["grain_air_delta_c"] = frame["grain_temp_c"] - frame["ambient_temp_c"]
    frame["hour_sin"] = np.sin(2 * np.pi * frame["hour_of_day"] / 24)
    frame["hour_cos"] = np.cos(2 * np.pi * frame["hour_of_day"] / 24)

    for source, target in (
        ("ambient_temp_c", "ambient_temp_rolling_6"),
        ("ambient_rh_pct", "ambient_rh_rolling_6"),
        ("grain_temp_c", "grain_temp_rolling_6"),
    ):
        frame[target] = frame.groupby("lot_id", sort=False)[source].transform(
            lambda values: values.rolling(window=6, min_periods=1).mean()
        )

    return frame.sort_values("_input_order")[list(MODEL_FEATURES)]
