from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, f1_score
from sklearn.model_selection import StratifiedGroupKFold

from ms_monitor_ai.features import MODEL_FEATURES, TARGET, build_features


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the MS-Monitor risk classifier.")
    parser.add_argument("--data", type=Path, default=Path("data/dataset.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("ai/artifacts"))
    return parser.parse_args()


def load_dataset(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Dataset not found: {path}")

    frame = pd.read_json(path)
    required = {
        "lot_id",
        "mold_mycotoxin_risk_level",
        "ambient_temp_c",
        "ambient_rh_pct",
        "grain_temp_c",
        "days_in_storage",
        "hour_of_day",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Dataset is missing columns: {', '.join(missing)}")
    if frame[list(required)].isnull().any().any():
        raise ValueError("Training columns cannot contain null values")
    return frame


def train(frame: pd.DataFrame) -> tuple[RandomForestClassifier, dict[str, object]]:
    features = build_features(frame)
    labels = frame[TARGET]

    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    train_indexes, test_indexes = next(
        splitter.split(features, labels, groups=frame["lot_id"])
    )

    model = RandomForestClassifier(
        n_estimators=250,
        min_samples_leaf=3,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(features.iloc[train_indexes], labels.iloc[train_indexes])
    predictions = model.predict(features.iloc[test_indexes])

    report = classification_report(
        labels.iloc[test_indexes],
        predictions,
        labels=list(model.classes_),
        output_dict=True,
        zero_division=0,
    )
    metrics: dict[str, object] = {
        "rows": len(frame),
        "lots": int(frame["lot_id"].nunique()),
        "features": list(MODEL_FEATURES),
        "classes": list(model.classes_),
        "test_lots": sorted(frame.iloc[test_indexes]["lot_id"].unique().tolist()),
        "accuracy": accuracy_score(labels.iloc[test_indexes], predictions),
        "balanced_accuracy": balanced_accuracy_score(labels.iloc[test_indexes], predictions),
        "macro_f1": f1_score(labels.iloc[test_indexes], predictions, average="macro"),
        "classification_report": report,
    }
    return model, metrics


def main() -> None:
    args = parse_args()
    frame = load_dataset(args.data)
    model, metrics = train(frame)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "features": list(MODEL_FEATURES),
            "classes": list(model.classes_),
        },
        args.output_dir / "risk_model.joblib",
    )
    (args.output_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Rows: {metrics['rows']} | Lots: {metrics['lots']}")
    print(f"Test lots: {', '.join(metrics['test_lots'])}")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Balanced accuracy: {metrics['balanced_accuracy']:.4f}")
    print(f"Macro F1: {metrics['macro_f1']:.4f}")
    print(f"Model saved to {args.output_dir / 'risk_model.joblib'}")


if __name__ == "__main__":
    main()
