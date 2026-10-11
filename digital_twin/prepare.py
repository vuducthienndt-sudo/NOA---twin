"""Prepare consented real-person video for NOA Digital Twin lip-sync tests.

Requirements: Python 3.10+, FFmpeg and ffprobe on PATH.
No GPU or paid service required. This does NOT synthesize a face or voice.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def run(command: list[str]) -> str:
    result = subprocess.run(command, check=True, text=True, capture_output=True)
    return result.stdout


def probe(path: Path) -> dict:
    return json.loads(run([
        "ffprobe", "-v", "error", "-show_streams", "-show_format",
        "-of", "json", str(path),
    ]))


def prepare(video: Path, audio: Path, output: Path, seconds: float, start: float) -> dict:
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            raise RuntimeError(f"{tool} is missing from PATH")
    for file in (video, audio):
        if not file.is_file():
            raise FileNotFoundError(file)
    if seconds <= 0 or start < 0:
        raise ValueError("seconds must be positive and start must be >= 0")
    vmeta, ameta = probe(video), probe(audio)
    if not any(s.get("codec_type") == "video" for s in vmeta["streams"]):
        raise ValueError("Input video has no video stream")
    if not any(s.get("codec_type") == "audio" for s in ameta["streams"]):
        raise ValueError("Input audio has no audio stream")
    vduration = float(vmeta["format"]["duration"])
    aduration = float(ameta["format"]["duration"])
    if start + seconds > vduration + 0.01:
        raise ValueError("Requested clip exceeds input video duration")
    if aduration < seconds - 0.1:
        raise ValueError("Audio is shorter than requested output")
    output.mkdir(parents=True, exist_ok=True)
    source = output / "source_25fps.mp4"
    speech = output / "speech_16k.wav"
    reference = output / "reference_frame.jpg"
    run(["ffmpeg", "-y", "-ss", str(start), "-i", str(video),
         "-t", str(seconds), "-vf", "fps=25",
         "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-crf", "18", str(source)])
    run(["ffmpeg", "-y", "-i", str(audio), "-t", str(seconds),
         "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(speech)])
    run(["ffmpeg", "-y", "-i", str(source), "-frames:v", "1", str(reference)])
    manifest = {
        "project": "NOA Digital Twin V1",
        "consent_required": True,
        "source_video": str(source.resolve()),
        "speech_audio": str(speech.resolve()),
        "reference_frame": str(reference.resolve()),
        "target_seconds": seconds,
        "fps": 25,
        "status": "prepared_not_rendered",
        "next_step": "Run approved lip-sync model, then compare with untouched source frames",
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--audio", type=Path, required=True,
                        help="Authorized speech audio; voice cloning is a separate stage")
    parser.add_argument("--out", type=Path, default=Path("outputs/test01"))
    parser.add_argument("--seconds", type=float, default=10)
    parser.add_argument("--start", type=float, default=0)
    parser.add_argument("--consent", action="store_true",
                        help="Confirm the person consented to this use of their likeness and voice")
    args = parser.parse_args()
    if not args.consent:
        parser.error("--consent is required")
    print(json.dumps(prepare(args.video, args.audio, args.out,
                             args.seconds, args.start), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
