import pandas as pd

from ms_monitor_ai.features import MODEL_FEATURES, build_features


def test_build_features_uses_sensor_values_and_preserves_row_order():
    rows = pd.DataFrame(
        [
            {
                "lot_id": "lot-b",
                "days_in_storage": 1,
                "hour_of_day": 0,
                "ambient_temp_c": 20.0,
                "ambient_rh_pct": 60.0,
                "grain_temp_c": 22.0,
            },
            {
                "lot_id": "lot-a",
                "days_in_storage": 0,
                "hour_of_day": 1,
                "ambient_temp_c": 24.0,
                "ambient_rh_pct": 70.0,
                "grain_temp_c": 25.0,
            },
        ]
    )

    result = build_features(rows)

    assert list(result.columns) == list(MODEL_FEATURES)
    assert result["grain_air_delta_c"].tolist() == [2.0, 1.0]
    assert result["ambient_temp_rolling_6"].tolist() == [20.0, 24.0]
