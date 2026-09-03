import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "build_style_bank_from_cv26.py"
SPEC = importlib.util.spec_from_file_location("build_style_bank_from_cv26", SCRIPT)
assert SPEC and SPEC.loader
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def test_selection_has_each_style_and_intensity_exactly_once() -> None:
    assert len(builder.SELECTIONS) == 21
    assert {(style, intensity) for style, intensity, _, _ in builder.SELECTIONS} == {
        (style, intensity)
        for style in ("neutral", "happy", "sad", "excited", "gentle", "serious", "surprised")
        for intensity in (1, 2, 3)
    }
    utterance_ids = [utt_id for _, _, utt_id, _ in builder.SELECTIONS]
    assert len(utterance_ids) == len(set(utterance_ids))
