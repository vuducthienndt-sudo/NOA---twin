"""Generate a source-vs-render contact sheet for human review.

This is visual evidence, not an automated identity or lip-sync verdict.
Requires OpenCV and numpy. No GPU needed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def video_info(path: Path):
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {path}")
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if fps <= 0 or count <= 0:
        cap.release()
        raise ValueError(f"Invalid video metadata: {path}")
    return cap, fps, count


def make_sheet(source: Path, rendered: Path, out: Path, samples: int = 8,
               tile_width: int = 480) -> dict:
    if samples < 2 or tile_width < 100:
        raise ValueError("samples must be >= 2 and tile_width >= 100")
    src, fps_a, n_a = video_info(source)
    dst, fps_b, n_b = video_info(rendered)
    try:
        duration = min(n_a / fps_a, n_b / fps_b)
        if duration <= 0:
            raise ValueError("Empty overlapping video duration")
        times = np.linspace(0, max(0, duration - 1 / max(fps_a, fps_b)), samples)
        panels = []
        for t in times:
            frames = []
            for cap, fps, count in ((src, fps_a, n_a), (dst, fps_b, n_b)):
                cap.set(cv2.CAP_PROP_POS_FRAMES, min(count - 1, int(round(float(t) * fps))))
                ok, frame = cap.read()
                if not ok:
                    raise RuntimeError(f"Cannot decode frame at {t:.2f}s")
                h, w = frame.shape[:2]
                new_h = int(round(h * tile_width / w))
                frame = cv2.resize(frame, (tile_width, new_h))
                frames.append(frame)
            height = max(a.shape[0] for a in frames)
            normalized = []
            for frame in frames:
                if frame.shape[0] != height:
                    pad = height - frame.shape[0]
                    frame = cv2.copyMakeBorder(frame, 0, pad, 0, 0,
                                               cv2.BORDER_CONSTANT, value=(20, 20, 20))
                normalized.append(frame)
            panel = np.hstack(normalized)
            cv2.putText(panel, f"{t:.2f}s | LEFT: ORIGINAL | RIGHT: AI", (12, 27),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2,
                        cv2.LINE_AA)
            panels.append(panel)
        sheet = np.vstack(panels)
        out.parent.mkdir(parents=True, exist_ok=True)
        if not cv2.imwrite(str(out), sheet):
            raise IOError(f"Could not save image: {out}")
        report = {
            "contact_sheet": str(out),
            "sample_times_seconds": [round(float(t), 3) for t in times],
            "source_fps": fps_a,
            "rendered_fps": fps_b,
            "source_frame_count": n_a,
            "rendered_frame_count": n_b,
            "warning": "Time-based matching is approximate; check temporal alignment manually.",
        }
        out.with_suffix(".json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return report
    finally:
        src.release()
        dst.release()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--rendered", type=Path, required=True)
    p.add_argument("--out", type=Path, default=Path("outputs/test01/contact_sheet.jpg"))
    p.add_argument("--samples", type=int, default=8)
    a = p.parse_args()
    print(json.dumps(make_sheet(a.source, a.rendered, a.out, a.samples),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
