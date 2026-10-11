"""Human review scorecard for NOA Digital Twin pilot renders.

The scores are human assessments, not automated claims of HeyGen parity.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CRITERIA = {
    "identity": 0.25,
    "vietnamese_lip_sync": 0.25,
    "mouth_teeth": 0.15,
    "temporal_stability": 0.15,
    "natural_motion": 0.10,
    "body_preservation": 0.10,
}
MINIMUM = {
    "identity": 4,
    "vietnamese_lip_sync": 4,
    "mouth_teeth": 3,
    "temporal_stability": 3,
    "natural_motion": 3,
    "body_preservation": 4,
}


def evaluate(scores: dict[str, int]) -> dict:
    if set(scores) != set(CRITERIA):
        raise ValueError("All six review criteria are required")
    for name, score in scores.items():
        if type(score) is not int or score < 1 or score > 5:
            raise ValueError(f"{name} must be an integer from 1 to 5")
    weighted = round(sum(scores[k] * CRITERIA[k] for k in CRITERIA), 2)
    failures = [key for key in CRITERIA if scores[key] < MINIMUM[key]]
    return {
        "weighted_score_out_of_5": weighted,
        "review_gate": "candidate_pass" if weighted >= 4 and not failures else "needs_improvement",
        "below_minimum": failures,
        "scores": scores,
        "note": "Human visual review only; not proof of identity, consent or audio sync.",
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scores", type=Path, required=True,
                   help="JSON mapping six criterion names to integer scores 1-5")
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = evaluate(json.loads(args.scores.read_text(encoding="utf-8")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
