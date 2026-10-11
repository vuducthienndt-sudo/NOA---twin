"""Reproducible comparison record for consented NOA Digital Twin experiments."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from digital_twin.heygen_scorecard import evaluate

MODELS = {"musetalk-v1.5", "reference-conditioned-research", "heygen-authorized-reference"}


def build_record(experiment_id: str, model: str, source_id: str,
                 speech_id: str, duration_seconds: float,
                 gpu_minutes: float, gpu_cost_vnd: float,
                 scores: dict[str, int] | None = None) -> dict:
    if not experiment_id or not source_id or not speech_id:
        raise ValueError("Experiment, source and speech IDs are required")
    if model not in MODELS:
        raise ValueError("Unknown model label")
    if not (0 < duration_seconds <= 60):
        raise ValueError("Duration must be 1-60 seconds")
    if gpu_minutes < 0 or gpu_cost_vnd < 0:
        raise ValueError("GPU usage and costs must not be negative")
    review = evaluate(scores) if scores is not None else None
    return {
        "experiment_id": experiment_id,
        "model": model,
        "source_asset_id": source_id,
        "speech_asset_id": speech_id,
        "duration_seconds": duration_seconds,
        "gpu_minutes": gpu_minutes,
        "gpu_cost_vnd": gpu_cost_vnd,
        "human_review": review,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "status": "reviewed" if review else "awaiting_human_review",
        "note": "Costs are user-entered measurements, not verified cloud billing.",
    }


def compare(records: list[dict]) -> dict:
    if len(records) < 2:
        raise ValueError("At least two experiment records are required")
    if len({(r["source_asset_id"], r["speech_asset_id"], r["duration_seconds"]) for r in records}) != 1:
        raise ValueError("Compare only matching source, audio and duration")
    reviewed = [r for r in records if r.get("human_review") is not None]
    ranked = sorted(reviewed, key=lambda r: (
        r["human_review"]["review_gate"] == "candidate_pass",
        r["human_review"]["weighted_score_out_of_5"],
        -r["gpu_cost_vnd"],
    ), reverse=True)
    return {
        "compared_models": [r["model"] for r in records],
        "reviewed_count": len(reviewed),
        "ranked": [
            {
                "model": r["model"],
                "experiment_id": r["experiment_id"],
                "quality_score": r["human_review"]["weighted_score_out_of_5"],
                "gate": r["human_review"]["review_gate"],
                "gpu_cost_vnd": r["gpu_cost_vnd"],
            }
            for r in ranked
        ],
        "note": "Ranking is based on human reviews, not an objective identity metric.",
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--records", type=Path, nargs="+", required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    records = [json.loads(path.read_text(encoding="utf-8")) for path in args.records]
    result = compare(records)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
