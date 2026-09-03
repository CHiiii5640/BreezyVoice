import importlib.util
import wave
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "preflight_style_bank.py"
SPEC = importlib.util.spec_from_file_location("preflight_style_bank", SCRIPT)
assert SPEC and SPEC.loader
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)


def write_reference(root: Path) -> None:
    path = root / "neutral"
    path.mkdir(parents=True)
    with wave.open(str(path / "2.wav"), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(b"\0\0" * 16000)
    (path / "2.txt").write_text("精確逐字稿", encoding="utf-8")


def test_preflight_reports_valid_audio_and_all_missing_entries(tmp_path: Path) -> None:
    write_reference(tmp_path)
    report = preflight.inspect(tmp_path)
    assert report["expected"] == 21
    assert report["ready"] is False
    assert report["valid"] == [{"style": "neutral", "intensity": 2, "path": str(tmp_path / "neutral" / "2.wav"),
                                 "seconds": 1.0, "sample_rate": 16000, "channels": 1, "sample_width": 2}]
    assert len(report["errors"]) == 20
