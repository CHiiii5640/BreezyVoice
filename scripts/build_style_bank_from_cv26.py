#!/usr/bin/env python3
"""Create a local-only 21-entry style bank from the selected CV26 speaker.

The labels are semantic candidates inferred from the exact transcript; Common
Voice is read speech, so they are not a claim that acoustic emotion was audited.
All generated WAVs and provenance remain excluded from git.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path


# style, intensity, utterance id, semantic rationale.  Every utterance is
# distinct and belongs to the 32.32-minute selected female speaker manifest.
SELECTIONS = (
    ("neutral", 1, "common_voice_zh-TW_18785115", "short factual statement"),
    ("neutral", 2, "common_voice_zh-TW_18785087", "measured recommendation"),
    ("neutral", 3, "common_voice_zh-TW_18784317", "formal factual statement"),
    ("happy", 1, "common_voice_zh-TW_18784524", "positive praise"),
    ("happy", 2, "common_voice_zh-TW_18784447", "birthday greeting"),
    ("happy", 3, "common_voice_zh-TW_18785326", "emphatic birthday greeting"),
    ("sad", 1, "common_voice_zh-TW_18785219", "negative caution"),
    ("sad", 2, "common_voice_zh-TW_18784324", "critical negative statement"),
    ("sad", 3, "common_voice_zh-TW_18784356", "explicit discouragement"),
    ("excited", 1, "common_voice_zh-TW_18784372", "enthusiastic praise"),
    ("excited", 2, "common_voice_zh-TW_18784306", "emphatic thanks"),
    ("excited", 3, "common_voice_zh-TW_18784560", "strong excitement; contains profanity"),
    ("gentle", 1, "common_voice_zh-TW_18785058", "casual thanks"),
    ("gentle", 2, "common_voice_zh-TW_18784360", "reassurance"),
    ("gentle", 3, "common_voice_zh-TW_18785316", "warm reassurance"),
    ("serious", 1, "common_voice_zh-TW_18784449", "formal judicial statement"),
    ("serious", 2, "common_voice_zh-TW_18785254", "formal rule announcement"),
    ("serious", 3, "common_voice_zh-TW_18785220", "firm mandatory statement"),
    ("surprised", 1, "common_voice_zh-TW_18784439", "light surprise question"),
    ("surprised", 2, "common_voice_zh-TW_18784344", "urgent surprise question"),
    ("surprised", 3, "common_voice_zh-TW_18784504", "explicit exclamation"),
)


def load_manifest(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return {row["utt_id"]: row for row in csv.DictReader(stream, delimiter="\t")}


def build(manifest_path: Path, output: Path, overwrite: bool) -> list[dict[str, object]]:
    manifest = load_manifest(manifest_path)
    ids = [item[2] for item in SELECTIONS]
    if len(ids) != len(set(ids)):
        raise ValueError("style-bank selection must contain distinct utterances")
    records: list[dict[str, object]] = []
    for style, intensity, utt_id, rationale in SELECTIONS:
        row = manifest.get(utt_id)
        if row is None:
            raise ValueError(f"selected utterance is absent from manifest: {utt_id}")
        source = Path(row["audio_path"])
        if not source.is_file():
            raise FileNotFoundError(source)
        directory = output / style
        directory.mkdir(parents=True, exist_ok=True)
        wav_path, text_path = directory / f"{intensity}.wav", directory / f"{intensity}.txt"
        if (wav_path.exists() or text_path.exists()) and not overwrite:
            raise FileExistsError(f"refusing to overwrite {style}/{intensity}; pass --overwrite")
        subprocess.run([
            "ffmpeg", "-nostdin", "-y" if overwrite else "-n", "-v", "error", "-i", str(source),
            "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(wav_path),
        ], check=True)
        text = row["text"].strip()
        text_path.write_text(text + "\n", encoding="utf-8")
        records.append({"style": style, "intensity": intensity, "utt_id": utt_id, "source": str(source),
                        "text": text, "duration_s": float(row["duration_s"]), "rationale": rationale,
                        "sha256": hashlib.sha256(wav_path.read_bytes()).hexdigest()})
    (output / "provenance.json").write_text(json.dumps({"source_manifest": str(manifest_path.resolve()),
        "speaker_minutes": 32.32, "semantic_labels_not_acoustic_verification": True, "entries": records},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/style_bank"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    records = build(args.manifest, args.output, args.overwrite)
    print(json.dumps({"created": len(records), "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
