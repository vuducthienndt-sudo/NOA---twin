"""Synthetic, CPU-only smoke test for NOA video preservation QA."""
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from digital_twin.quality_check import inspect


def make_video(path: Path, altered: bool = False) -> None:
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 25, (160, 120))
    if not writer.isOpened():
        raise RuntimeError("OpenCV video writer unavailable")
    try:
        for i in range(8):
            frame = np.full((120, 160, 3), 80, dtype=np.uint8)
            frame[20:50, 30:65] = 110 + i
            frame[65:85, 65:105] = 150
            if altered:
                frame[:60, :60] = 240
            writer.write(frame)
    finally:
        writer.release()


class QualityCheckTest(unittest.TestCase):
    def test_identical_video_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            video = root / "source.mp4"
            make_video(video)
            report = inspect(video, video, root / "qa.json", (.4, .5, .3, .25))
            self.assertEqual(report["automated_preservation_gate"], "pass")
            self.assertEqual(report["frame_count"], 8)

    def test_large_outside_change_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, rendered = root / "source.mp4", root / "rendered.mp4"
            make_video(source)
            make_video(rendered, altered=True)
            report = inspect(source, rendered, root / "qa.json", (.4, .5, .3, .25))
            self.assertEqual(report["automated_preservation_gate"], "fail")


if __name__ == "__main__":
    unittest.main()
