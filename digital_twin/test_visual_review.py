"""CPU smoke test for side-by-side source/render contact sheets."""
import tempfile
import unittest
from pathlib import Path

import cv2

from digital_twin.test_quality_check import make_video
from digital_twin.visual_review import make_sheet


class VisualReviewTests(unittest.TestCase):
    def test_generates_contact_sheet(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src, dst = root / "src.mp4", root / "dst.mp4"
            make_video(src)
            make_video(dst, altered=True)
            out = root / "comparison.jpg"
            report = make_sheet(src, dst, out, samples=3, tile_width=160)
            self.assertTrue(out.is_file())
            self.assertTrue(out.with_suffix(".json").is_file())
            self.assertEqual(len(report["sample_times_seconds"]), 3)
            self.assertIsNotNone(cv2.imread(str(out)))


if __name__ == "__main__":
    unittest.main()
