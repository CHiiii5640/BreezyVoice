from pathlib import Path

import pytest

from style_registry import StyleBankError, StyleRegistry


def reference(root: Path, style: str, intensity: int, text: str = "精確逐字稿") -> None:
    path = root / style
    path.mkdir(parents=True, exist_ok=True)
    (path / f"{intensity}.wav").write_bytes(b"wav")
    (path / f"{intensity}.txt").write_text(text, encoding="utf-8")


def test_default_neutral_and_cached_once(tmp_path: Path) -> None:
    reference(tmp_path, "neutral", 2)
    calls: list[str] = []
    registry = StyleRegistry(tmp_path, lambda path, rate: calls.append(path) or (path, rate))
    first = registry.resolve("neutral", 2)
    second = registry.resolve("neutral", 2)
    assert first is second
    assert first.transcript == "精確逐字稿"
    assert calls == [str(tmp_path / "neutral" / "2.wav")]


def test_preload_initializes_each_available_reference_once(tmp_path: Path) -> None:
    reference(tmp_path, "happy", 1, "快樂逐字稿")
    reference(tmp_path, "sad", 3, "難過逐字稿")
    calls: list[str] = []
    registry = StyleRegistry(tmp_path, lambda path, rate: calls.append(path) or path)
    registry.preload()
    assert calls == [str(tmp_path / "happy" / "1.wav"), str(tmp_path / "sad" / "3.wav")]
    assert registry.resolve("happy", 1).transcript == "快樂逐字稿"
    assert registry.resolve("sad", 3).transcript == "難過逐字稿"


@pytest.mark.parametrize("style", ["neutral", "happy", "sad", "excited", "gentle", "serious", "surprised"])
@pytest.mark.parametrize("intensity", [1, 2, 3])
def test_all_legal_style_intensity_pairs(tmp_path: Path, style: str, intensity: int) -> None:
    reference(tmp_path, style, intensity)
    prompt = StyleRegistry(tmp_path, lambda path, rate: path).resolve(style, intensity)
    assert (prompt.style, prompt.intensity) == (style, intensity)


@pytest.mark.parametrize("style,intensity", [("angry", 2), ("neutral", 4)])
def test_unknown_style_or_invalid_intensity_is_rejected(tmp_path: Path, style: str, intensity: int) -> None:
    with pytest.raises(StyleBankError):
        StyleRegistry(tmp_path, lambda path, rate: path).resolve(style, intensity)


@pytest.mark.parametrize("with_audio,transcript", [(False, "text"), (True, ""), (True, None)])
def test_missing_audio_or_transcript_is_rejected(tmp_path: Path, with_audio: bool, transcript: str | None) -> None:
    if with_audio:
        reference(tmp_path, "neutral", 2, transcript or "")
        if transcript is None:
            (tmp_path / "neutral" / "2.txt").unlink()
    with pytest.raises(StyleBankError):
        StyleRegistry(tmp_path, lambda path, rate: path).resolve("neutral", 2)
