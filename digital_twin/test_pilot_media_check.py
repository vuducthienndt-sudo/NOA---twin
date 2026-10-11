"""Unit tests for ffprobe pilot validation without external media."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from digital_twin.pilot_media_check import inspect_media, inspect_pilot


class PilotMediaCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.video = Path(self.tmp.name) / "source.mp4"
        self.audio = Path(self.tmp.name) / "audio.wav"
        self.video.write_bytes(b"placeholder")
        self.audio.write_bytes(b"placeholder")

    def tearDown(self):
        self.tmp.cleanup()

    def fake_probe(self, command, **kwargs):
        path = command[-1]
        if path.endswith(".mp4"):
            payload = {"format": {"duration": "10.0"}, "streams": [
                {"codec_type": "video", "width": 720, "height": 1280,
                 "r_frame_rate": "25/1"}]}
        else:
            payload = {"format": {"duration": "10.0"}, "streams": [
                {"codec_type": "audio", "sample_rate": "16000"}]}
        return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")

    @patch("digital_twin.pilot_media_check.subprocess.run")
    def test_valid_pair(self, mock_run):
        mock_run.side_effect = self.fake_probe
        result = inspect_pilot(self.video, self.audio)
        self.assertEqual(result["status"], "media_checked_not_rendered")
        self.assertFalse(result["consent_verified"])

    @patch("digital_twin.pilot_media_check.subprocess.run")
    def test_missing_video_stream(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            [], 0, json.dumps({"format": {"duration": "10"},
                               "streams": [{"codec_type": "audio"}]}), "")
        with self.assertRaises(ValueError):
            inspect_media(self.video, "video")

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            inspect_media(self.video.with_name("missing.mp4"), "video")


if __name__ == "__main__":
    unittest.main()
