"""Lightweight reference-frame selection inspired by video-reference research.

This is NOT HeyGen Sparse Reference Attention or TAVR inference.
Requires: OpenCV (`pip install opencv-python-headless`).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def pick_frames(video: Path, out: Path, count: int = 8,
                stride: int = 5, min_sharpness: float = 35.0) -> list[dict]:
    if count < 1 or stride < 1:
        raise ValueError("count and stride must be positive")
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise FileNotFoundError(f"Cannot open video: {video}")
    fps = capture.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        capture.release()
        raise ValueError("Invalid video FPS")
    candidates: list[dict] = []
    frame_id = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if frame_id % stride == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
                brightness = float(gray.mean())
                if sharpness >= min_sharpness and 35 <= brightness <= 220:
                    small = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA)
                    candidates.append({
                        "index": frame_id,
                        "seconds": round(frame_id / fps, 3),
                        "sharpness": round(sharpness, 2),
                        "descriptor": small.astype(np.float32).flatten(),
                        "frame": frame.copy(),
                    })
            frame_id += 1
    finally:
        capture.release()
    if not candidates:
        raise ValueError("No usable frames; lower --min-sharpness or check lighting")
    # Select high-quality frames with temporal spread and appearance diversity.
    selected = [max(candidates, key=lambda c: c["sharpness"])]
    while len(selected) < min(count, len(candidates)):
        remaining = [c for c in candidates if c["index"] not in
                     {s["index"] for s in selected}]
        if not remaining:
            break
        def score(c: dict) -> float:
            appearance = min(float(np.mean(np.abs(c["descriptor"] - s["descriptor"])))
                             for s in selected)
            temporal = min(abs(c["index"] - s["index"]) / fps for s in selected)
            return appearance + 2 * min(temporal, 5) + min(c["sharpness"] / 100, 10)
        selected.append(max(remaining, key=score))
    out.mkdir(parents=True, exist_ok=True)
    result = []
    for i, c in enumerate(sorted(selected, key=lambda c: c["index"])):
        name = f"reference_{i:02d}.jpg"
        if not cv2.imwrite(str(out / name), c["frame"]):
            raise IOError(f"Could not write {name}")
        result.append({k: c[k] for k in ("index", "seconds", "sharpness")} |
                      {"file": name})
    (out / "references.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("outputs/test01/references"))
    parser.add_argument("--count", type=int, default=8)
    parser.add_argument("--stride", type=int, default=5)
    parser.add_argument("--min-sharpness", type=float, default=35)
    args = parser.parse_args()
    print(json.dumps(pick_frames(args.video, args.out, args.count,
                                 args.stride, args.min_sharpness),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
