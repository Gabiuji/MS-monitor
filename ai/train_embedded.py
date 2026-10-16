"""Train the classroom embedded baseline without overwriting the Python baseline."""

import argparse
import hashlib
import json
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, f1_score
from sklearn.model_selection import StratifiedGroupKFold

from ms_monitor_ai.embedded import build_embedded_features, export_forest
from ms_monitor_ai.features import TARGET
from train import load_dataset


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/dataset.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("ai/artifacts"))
    parser.add_argument("--header", type=Path, default=Path("firmware/ms_monitor/risk_model.h"))
    parser.add_argument("--report", type=Path, default=Path("docs/embedded-ai-metrics.json"))
    args = parser.parse_args()
    frame = load_dataset(args.data)
    features = build_embedded_features(frame)
    labels = frame[TARGET]
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    train_index, test_index = next(splitter.split(features, labels, groups=frame["lot_id"]))
    model = RandomForestClassifier(n_estimators=32, max_depth=6, min_samples_leaf=5,
                                   class_weight="balanced_subsample", random_state=42, n_jobs=-1)
    model.fit(features.iloc[train_index], labels.iloc[train_index])
    predictions = model.predict(features.iloc[test_index])
    header, metadata = export_forest(model)
    metrics = metadata | dict(
        dataset_sha256=hashlib.sha256(args.data.read_bytes()).hexdigest(),
        training_config=model.get_params(),
        rows=len(frame), train_lots=sorted(frame.iloc[train_index]["lot_id"].unique().tolist()),
        test_lots=sorted(frame.iloc[test_index]["lot_id"].unique().tolist()),
        accuracy=accuracy_score(labels.iloc[test_index], predictions),
        balanced_accuracy=balanced_accuracy_score(labels.iloc[test_index], predictions),
        macro_f1=f1_score(labels.iloc[test_index], predictions, labels=model.classes_, average="macro", zero_division=0),
        classification_report=classification_report(labels.iloc[test_index], predictions,
            labels=model.classes_, output_dict=True, zero_division=0),
        limitations=["Classroom baseline; not validated with physical grain storage experiments.",
                     "Test metrics do not establish performance for classes absent from test lots."],
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.header.parent.mkdir(parents=True, exist_ok=True)
    args.header.write_text(header, encoding="utf-8")
    joblib.dump(dict(model=model, **metadata), args.output_dir / "embedded_risk_model.joblib")
    (args.output_dir / "embedded_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: metrics[key] for key in ["model_version", "trees", "nodes", "accuracy", "balanced_accuracy", "macro_f1"]}, indent=2))
    print(f"Generated firmware header: {args.header}")


if __name__ == "__main__":
    main()
