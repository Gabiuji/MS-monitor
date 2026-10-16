from pathlib import Path
import shutil
import subprocess

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier

from ms_monitor_ai.embedded import EMBEDDED_FEATURES, build_embedded_features, export_forest


def test_embedded_features_match_float_sensor_arithmetic():
    frame = pd.DataFrame(dict(ambient_temp_c=[24.8, 0], ambient_rh_pct=[59.2, 0], grain_temp_c=[25.25, 0]))
    features = build_embedded_features(frame)
    assert list(features.columns) == list(EMBEDDED_FEATURES)
    assert features.to_numpy().dtype == np.float32
    assert features.iloc[0, 3] == np.float32(25.25) - np.float32(24.8)
    assert features.iloc[1].tolist() == [0, 0, 0, 0]
    with pytest.raises(ValueError):
        build_embedded_features(frame.assign(ambient_temp_c=np.nan))


def test_export_is_reproducible_and_has_model_fingerprint():
    features = np.array([[index, index * 2, index + 1, 1] for index in range(16)], dtype=np.float32)
    labels = np.tile(["low", "moderate", "high", "critical"], 4)
    model = RandomForestClassifier(n_estimators=3, max_depth=3, random_state=42).fit(features, labels)
    header, metadata = export_forest(model)
    assert export_forest(model) == (header, metadata)
    assert metadata["model_version"].startswith("embedded-rf-")
    assert metadata["model_version"] in header
    assert metadata["features"] == list(EMBEDDED_FEATURES)
    incompatible = RandomForestClassifier(n_estimators=1, random_state=42).fit(features[:, :3], labels)
    with pytest.raises(ValueError):
        export_forest(incompatible)


def test_native_predictor_rejects_invalid_sensors_and_accepts_zero(tmp_path):
    compiler = shutil.which("g++")
    if compiler is None:
        pytest.skip("Native C++ compiler is not installed")
    root = Path(__file__).resolve().parents[2]
    source = tmp_path / "check.cpp"
    source.write_text('''
#include <assert.h>
#include <math.h>
#include "embedded_inference.h"
int main() {
  using namespace ms_monitor_ai;
  auto result = predictRisk(0, 0, 0);
  assert(result.valid);
  float sum = 0;
  for (float value : result.probabilities) { assert(value >= 0 && value <= 1); sum += value; }
  assert(fabs(sum - 1) < 0.000001);
  assert(result.confidence >= 0 && result.confidence <= 1);
  assert(result.riskScore >= 0 && result.riskScore <= 1);
  assert(!predictRisk(NAN, 50, 25).valid);
  assert(!predictRisk(25, INFINITY, 25).valid);
  assert(!predictRisk(25, 50, NAN).valid);
  assert(!predictRisk(-41, 50, 25).valid);
  assert(!predictRisk(25, 101, 25).valid);
  assert(!predictRisk(25, 50, -1).valid);
  assert(!predictRisk(25, 50, 1025).valid);
  assert(predictRisk(80, 100, 1024).valid);
  return 0;
}
''', encoding="utf-8")
    executable = tmp_path / "check"
    subprocess.run([compiler, "-std=c++11", "-O2", "-Wall", "-Wextra", "-Werror", "-I",
                    str(root / "firmware/ms_monitor"), str(source), "-o", str(executable)], check=True)
    subprocess.run([str(executable)], check=True)
