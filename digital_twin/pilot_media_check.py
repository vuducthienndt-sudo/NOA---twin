"""Inspect authorized pilot media before spending GPU time."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def inspect_media(path: Path, kind: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(path)
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,width,height,r_frame_rate,sample_rate",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True, timeout=30,
    )
    data = json.loads(proc.stdout)
    streams = data.get("streams", [])
    matching = [s for s in streams if s.get("codec_type") == kind]
    if not matching:
        raise ValueError(f"No {kind} stream found")
    duration = float(data.get("format", {}).get("duration", 0))
    if not (0 < duration <= 60):
        raise ValueError("Pilot input duration must be 0-60 seconds")
    stream = matching[0]
    result = {"path": str(path.resolve()), "duration_seconds": round(duration, 3),
              "stream_type": kind}
    if kind == "video":
        width, height = int(stream.get("width", 0)), int(stream.get("height", 0))
        if width < 256 or height < 256:
            raise ValueError("Video resolution is too low")
        result.update({"width": width, "height": height,
                       "frame_rate": stream.get("r_frame_rate")})
    else:
        result["sample_rate"] = int(stream.get("sample_rate", 0))
        if result["sample_rate"] < 8000:
            raise ValueError("Audio sample rate is too low")
    return result


def inspect_pilot(video: Path, audio: Path) -> dict:
    v = inspect_media(video, "video")
    a = inspect_media(audio, "audio")
    if abs(v["duration_seconds"] - a["duration_seconds"]) > 2:
        raise ValueError("Audio and video durations differ by more than 2 seconds")
    return {"status": "media_checked_not_rendered", "video": v, "audio": a,
            "consent_verified": False,
            "note": "Technical inspection does not establish legal consent or identity."}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--video", type=Path, required=True)
    p.add_argument("--audio", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = inspect_pilot(args.video, args.audio)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
