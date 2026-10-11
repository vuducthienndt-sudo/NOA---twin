"""CPU tests for the single-task MuseTalk 1.5 adapter."""
import unittest
import json
from pathlib import Path
from digital_twin.run_musetalk import build_config


class AdapterTests(unittest.TestCase):
    def test_single_task_from_official_two_task_template(self):
        upstream = (
            "task_0:\n"
            " video_path: data/video/yongen.mp4\n"
            " audio_path: data/audio/yongen.wav\n"
            "task_1:\n"
            " video_path: data/video/yongen.mp4\n"
            " audio_path: data/audio/eng.wav\n"
            " bbox_shift: -7\n"
        )
        result = build_config(upstream, Path("/tmp/a.mp4"), Path("/tmp/b.wav"))
        self.assertEqual(result.count("task_0:"), 1)
        self.assertNotIn("task_1:", result)
        self.assertIn("video_path: " + json.dumps(str(Path("/tmp/a.mp4"))), result)
        self.assertIn("audio_path: " + json.dumps(str(Path("/tmp/b.wav"))), result)
        self.assertEqual(result.count("video_path:"), 1)
        self.assertEqual(result.count("audio_path:"), 1)


if __name__ == "__main__":
    unittest.main()
