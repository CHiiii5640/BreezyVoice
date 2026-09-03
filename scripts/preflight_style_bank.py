#!/usr/bin/env python3
"""Validate an authorized BreezyVoice style bank before model startup.

This checks files and WAV decodability only.  The operator remains responsible
for ensuring every clip is from the same authorized speaker and every transcript
is exact.
"""

from __future__ import annotations

import argparse
import json
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from style_registry import INTENSITIES, STYLES


def inspect(root: Path) -> dict[str, object]:
    valid: list[dict[str, object]] = []
    errors: list[str] = []
    for style in STYLES:
        for intensity in INTENSITIES:
            base = root / style / str(intensity)
            wav_path, text_path = base.with_suffix(".wav"), base.with_suffix(".txt")
            label = f"{style}/{intensity}"
            if not wav_path.is_file():
                errors.append(f"{label}: missing WAV")
                continue
            if not text_path.is_file():
                errors.append(f"{label}: missing exact transcript")
                continue
            if not text_path.read_text(encoding="utf-8").strip():
                errors.append(f"{label}: empty exact transcript")
                continue
            try:
                with wave.open(str(wav_path), "rb") as audio:
                    frames, rate = audio.getnframes(), audio.getframerate()
                    valid.append({"style": style, "intensity": intensity, "path": str(wav_path),
                                  "seconds": round(frames / rate, 3), "sample_rate": rate,
                                  "channels": audio.getnchannels(), "sample_width": audio.getsampwidth()})
            except (wave.Error, EOFError) as error:
                errors.append(f"{label}: undecodable WAV ({error})")
    return {"root": str(root), "expected": len(STYLES) * len(INTENSITIES), "valid": valid, "errors": errors,
            "ready": not errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path("data/style_bank"))
    report = inspect(parser.parse_args().root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
