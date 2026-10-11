"""MuseTalk 1.5 adapter for prepared NOA Digital Twin assets.

Uses MuseTalk's documented scripts.inference CLI and YAML configuration.
No model download, GPU rental, or execution unless --execute is supplied.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def quote_yaml(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def build_config(base_yaml: str, video: Path, audio: Path) -> str:
    """Generate exactly one MuseTalk task, avoiding duplicate demo renders.

    MuseTalk's official sample YAML contains task_0 and task_1. Copying it
    verbatim would accidentally run the user's audio twice.
    """
    return (
        "task_0:\n"
        f"  video_path: {quote_yaml(str(video))}\n"
        f"  audio_path: {quote_yaml(str(audio))}\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--musetalk-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("outputs/test01/musetalk"))
    parser.add_argument("--execute", action="store_true",
                        help="Actually launch GPU inference (default: prepare only)")
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if not manifest.get("consent_required"):
        raise ValueError("Missing consent metadata")
    video = Path(manifest["source_video"]).resolve()
    audio = Path(manifest["speech_audio"]).resolve()
    if not video.is_file() or not audio.is_file():
        raise FileNotFoundError("Prepared video/audio missing; run prepare.py first")
    root = args.musetalk_dir.resolve()
    base = root / "configs/inference/test.yaml"
    model = root / "models/musetalkV15/unet.pth"
    model_config = root / "models/musetalkV15/musetalk.json"
    if not base.is_file():
        raise FileNotFoundError(f"Official MuseTalk configuration missing: {base}")
    args.out.mkdir(parents=True, exist_ok=True)
    generated = args.out.resolve() / "noa_test.yaml"
    generated.write_text(build_config(base.read_text(encoding="utf-8"), video, audio),
                         encoding="utf-8")
    command = [
        sys.executable, "-m", "scripts.inference",
        "--inference_config", str(generated),
        "--result_dir", str((args.out / "results").resolve()),
        "--unet_model_path", str(model),
        "--unet_config", str(model_config),
        "--version", "v15",
    ]
    report = {
        "status": "configured_not_rendered",
        "command": command,
        "cwd": str(root),
        "config": str(generated),
        "note": "Output is not verified until the model runs and the video is inspected",
    }
    (args.out / "run_plan.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not args.execute:
        return
    if not model.is_file() or not model_config.is_file():
        raise FileNotFoundError("MuseTalk 1.5 weights missing; follow upstream download instructions")
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg missing")
    subprocess.run(command, cwd=root, check=True)


if __name__ == "__main__":
    main()
