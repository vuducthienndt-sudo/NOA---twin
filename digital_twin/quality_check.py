"""NOA Digital Twin output QA: source preservation and temporal stability.

Compares synchronized source/rendered frames. Pixel measurements are diagnostic,
NOT a biometric identity score or proof that a face is unchanged.

Install: pip install -r digital_twin/requirements-references.txt
Run: python digital_twin/quality_check.py --source ... --rendered ... --out ...
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def _frames(path: Path):
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {path}")
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            raise ValueError(f"Invalid frame rate: {path}")
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            yield frame, fps
    finally:
        cap.release()


def inspect(source: Path, rendered: Path, out: Path, mouth_box: tuple[float, float, float, float],
            max_outside_mae: float = 12.0, max_temporal_delta: float = 8.0) -> dict:
    x, y, w, h = mouth_box
    if not (0 <= x < 1 and 0 <= y < 1 and 0 < w <= 1-x and 0 < h <= 1-y):
        raise ValueError("Mouth box must be normalized x,y,w,h inside the frame")
    source_iter, render_iter = _frames(source), _frames(rendered)
    count, outside_errors, flicker_errors = 0, [], []
    prev_source, prev_render = None, None
    source_fps, render_fps = None, None
    while True:
        a = next(source_iter, None)
        b = next(render_iter, None)
        if a is None and b is None:
            break
        if a is None or b is None:
            raise ValueError("Source and rendered video have different frame counts")
        src, source_fps = a
        dst, render_fps = b
        if src.shape != dst.shape:
            raise ValueError("Source and rendered frame sizes differ")
        if abs(source_fps - render_fps) > 0.01:
            raise ValueError("Source and rendered FPS differ")
        height, width = src.shape[:2]
        x0, y0 = int(x*width), int(y*height)
        x1, y1 = min(width, int((x+w)*width)), min(height, int((y+h)*height))
        mask = np.ones((height, width), dtype=bool)
        mask[y0:y1, x0:x1] = False
        if not mask.any():
            raise ValueError("Mouth box covers entire frame")
        src_f = src.astype(np.float32)
        dst_f = dst.astype(np.float32)
        outside_errors.append(float(np.abs(src_f-dst_f)[mask].mean()))
        if prev_source is not None:
            # Excess temporal change outside the mouth area compared to real motion.
            source_motion = src_f - prev_source
            render_motion = dst_f - prev_render
            flicker_errors.append(float(np.abs(source_motion-render_motion)[mask].mean()))
        prev_source, prev_render = src_f, dst_f
        count += 1
    if count == 0:
        raise ValueError("Video is empty")
    outside_mae = float(np.mean(outside_errors))
    temporal_delta = float(np.mean(flicker_errors)) if flicker_errors else 0.0
    report = {
        "status": "review_required",
        "frame_count": count,
        "fps": source_fps,
        "mouth_box_normalized": list(mouth_box),
        "outside_mouth_mean_absolute_error_0_255": round(outside_mae, 3),
        "outside_mouth_temporal_delta_0_255": round(temporal_delta, 3),
        "thresholds": {
            "max_outside_mae": max_outside_mae,
            "max_temporal_delta": max_temporal_delta,
        },
        "automated_preservation_gate": (
            "pass" if outside_mae <= max_outside_mae and temporal_delta <= max_temporal_delta
            else "fail"
        ),
        "limitations": [
            "The mouth box is a fixed manual ROI, not face tracking.",
            "Camera movement, compression and frame timing affect pixel metrics.",
            "No voice, lip-sync, teeth, eye or biometric identity assessment is performed.",
            "A pass is not permission to publish; human review is required.",
        ],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--rendered", type=Path, required=True)
    p.add_argument("--out", type=Path, default=Path("outputs/test01/qa.json"))
    p.add_argument("--mouth-box", type=float, nargs=4, default=(0.3, 0.48, 0.4, 0.2),
                   metavar=("X", "Y", "W", "H"),
                   help="Normalized manual mouth ROI; adjust for each video")
    p.add_argument("--max-outside-mae", type=float, default=12.0)
    p.add_argument("--max-temporal-delta", type=float, default=8.0)
    a = p.parse_args()
    print(json.dumps(inspect(a.source, a.rendered, a.out, tuple(a.mouth_box),
                             a.max_outside_mae, a.max_temporal_delta),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
