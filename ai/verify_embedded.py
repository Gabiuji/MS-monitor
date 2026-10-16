"""Compare the real C++ predictor against sklearn on the complete local dataset."""

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

import joblib
import numpy as np

from ms_monitor_ai.embedded import build_embedded_features
from train import load_dataset


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/dataset.json"))
    parser.add_argument("--model", type=Path, default=Path("ai/artifacts/embedded_risk_model.joblib"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    bundle = joblib.load(args.model)
    model = bundle["model"]
    frame = load_dataset(args.data)
    features = build_embedded_features(frame)
    inputs = features.iloc[:, :3].to_numpy()
    with tempfile.TemporaryDirectory(prefix="ms-monitor-inference-") as directory:
        executable = Path(directory) / "verify"
        subprocess.run(["g++", "-std=c++11", "-O2", "-Wall", "-Wextra", "-Werror",
                        "-I", str(root / "firmware/ms_monitor"), str(root / "ai/verify_embedded.cpp"),
                        "-o", str(executable)], check=True)
        info = subprocess.check_output([str(executable), "--info"], text=True).strip()
        if bundle["model_version"] not in info:
            raise RuntimeError("The firmware header does not match the Python model version")
        source = "\n".join(" ".join(format(float(value), ".9g") for value in row) for row in inputs)
        output = subprocess.check_output([str(executable)], input=source, text=True)
    results = np.array([line.split() for line in output.splitlines()], dtype=float)
    probabilities = model.predict_proba(features)
    expected_classes = np.argmax(probabilities, axis=1)
    mismatches = int(np.count_nonzero(results[:, 0] != expected_classes))
    error = float(np.max(np.abs(results[:, 1:5] - probabilities)))
    if mismatches or error > 1e-6:
        raise RuntimeError(f"C++ parity failed: {mismatches} class mismatches, probability error {error}")
    report = dict(samples=len(frame), class_mismatches=mismatches, max_probability_error=error,
                  model=bundle["model_version"], compiled_model=info)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
