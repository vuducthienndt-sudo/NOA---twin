"""Read-only GPU preflight and cost estimator for NOA Digital Twin.

Does not create a GPU instance, download weights, or run inference.
The hourly rate must be provided by the operator from the actual rental quote.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def gpu_info() -> list[dict]:
    if not shutil.which("nvidia-smi"):
        return []
    command = [
        "nvidia-smi",
        "--query-gpu=name,memory.total,memory.free",
        "--format=csv,noheader,nounits",
    ]
    try:
        lines = subprocess.run(command, check=True, capture_output=True,
                               text=True, timeout=10).stdout.splitlines()
    except (OSError, subprocess.SubprocessError):
        return []
    result = []
    for line in lines:
        parts = [s.strip() for s in line.split(",")]
        if len(parts) != 3:
            continue
        try:
            result.append({"name": parts[0], "total_mib": int(parts[1]),
                           "free_mib": int(parts[2])})
        except ValueError:
            continue
    return result


def estimate(hourly_usd: float, hours: float, vnd_per_usd: float,
             cap_vnd: float) -> dict:
    if min(hourly_usd, hours, vnd_per_usd, cap_vnd) < 0 or vnd_per_usd == 0:
        raise ValueError("Price, duration, exchange rate and cap must be valid")
    projected = hourly_usd * hours * vnd_per_usd
    return {
        "hourly_usd_user_supplied": hourly_usd,
        "hours_user_supplied": hours,
        "vnd_per_usd_user_supplied": vnd_per_usd,
        "projected_vnd": round(projected),
        "cap_vnd": cap_vnd,
        "within_cap": projected <= cap_vnd,
        "exclusions": ["Storage", "Network egress", "Taxes", "Idle billing"],
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--hourly-usd", type=float, required=True)
    p.add_argument("--hours", type=float, required=True)
    p.add_argument("--vnd-per-usd", type=float, required=True,
                   help="Use your actual payment/FX rate; do not assume a live rate")
    p.add_argument("--cap-vnd", type=float, default=200000)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    report = {
        "gpu": gpu_info(),
        "budget": estimate(args.hourly_usd, args.hours, args.vnd_per_usd,
                           args.cap_vnd),
        "status": "estimate_only_no_gpu_launched",
    }
    result = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(result, encoding="utf-8")
    print(result)
    if not report["budget"]["within_cap"]:
        raise SystemExit("Budget estimate exceeds cap; do not start GPU")


if __name__ == "__main__":
    main()
