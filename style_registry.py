"""Authorized reference-audio style bank for the BreezyVoice API.

Copyright 2026 CHiiii5640
Licensed under the Apache License, Version 2.0.  This file is an addition to
the upstream MediaTek Research BreezyVoice project.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable


STYLES = ("neutral", "happy", "sad", "excited", "gentle", "serious", "surprised")
INTENSITIES = (1, 2, 3)


class StyleBankError(ValueError):
    """A request cannot be served without an explicitly authorized reference."""


@dataclass(frozen=True)
class PromptReference:
    style: str
    intensity: int
    audio_path: Path
    transcript: str
    prompt_speech_16k: object


class StyleRegistry:
    """Loads each valid WAV once and never substitutes another speaker/style."""

    def __init__(self, root: str | Path, load_wav: Callable[[str, int], object]) -> None:
        self.root = Path(root)
        self._load_wav = load_wav
        self._cache: dict[tuple[str, int], PromptReference] = {}

    def preload(self) -> None:
        for style in STYLES:
            for intensity in INTENSITIES:
                try:
                    self._cache[(style, intensity)] = self._read(style, intensity)
                except StyleBankError:
                    # Invalid or incomplete references must produce request-time
                    # HTTP 422, never make every other authorized style unusable.
                    continue

    def resolve(self, style: str, intensity: int) -> PromptReference:
        if style not in STYLES:
            raise StyleBankError(f"unknown style: {style}")
        if intensity not in INTENSITIES:
            raise StyleBankError(f"intensity must be 1, 2, or 3: {intensity}")
        key = (style, intensity)
        if key not in self._cache:
            self._cache[key] = self._read(style, intensity)
        return self._cache[key]

    def _paths(self, style: str, intensity: int) -> tuple[Path, Path]:
        base = self.root / style / str(intensity)
        return base.with_suffix(".wav"), base.with_suffix(".txt")

    def _read(self, style: str, intensity: int) -> PromptReference:
        audio_path, transcript_path = self._paths(style, intensity)
        if not audio_path.is_file():
            raise StyleBankError(f"missing authorized WAV: {audio_path}")
        if not transcript_path.is_file():
            raise StyleBankError(f"missing exact transcript: {transcript_path}")
        transcript = transcript_path.read_text(encoding="utf-8").strip()
        if not transcript:
            raise StyleBankError(f"empty exact transcript: {transcript_path}")
        return PromptReference(style, intensity, audio_path, transcript, self._load_wav(str(audio_path), 16000))
