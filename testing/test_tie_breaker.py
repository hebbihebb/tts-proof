import json
from pathlib import Path

import pytest

from mdp.tie_breaker import (
    DecisionLogger,
    detect_hazards,
    postcheck,
    tie_break,
)


def test_detect_hazards_spaced_letters():
    text = "[F ʟ ᴀ s ʜ D ᴀ ɴ ᴄ ᴇ] returns soon"
    hazards = detect_hazards(text)
    assert any(span.reason == "spaced_letters" for span in hazards)


def test_tie_break_rejects_tts_hazard(tmp_path: Path):
    prepass = "The [Flash Dance] revival"
    grammar = "The [Flash Dance] revival"
    tts = "The [F ʟ ᴀ s ʜ  D ᴀ ɴ ᴄ ᴇ] revival"

    logger = DecisionLogger(tmp_path / "decision-log.ndjson")
    hazard_mask = detect_hazards(prepass)

    final_text, stats = tie_break(prepass, grammar, tts, hazard_mask, logger)

    assert "[Flash Dance]" in final_text
    assert "F ʟ ᴀ s ʜ" not in final_text
    assert stats["tts"]["skipped"] >= 1

    log_contents = (tmp_path / "decision-log.ndjson").read_text(encoding="utf-8").strip().splitlines()
    assert log_contents, "Decision log should contain at least one entry"
    last_entry = json.loads(log_contents[-1])
    assert last_entry["stage"] == "tts-fixer"
    assert last_entry["rule"].startswith("skip")


def test_tie_break_applies_grammar_change():
    prepass = "He say hello."
    grammar = "He says hello."
    tts = "He says hello."

    logger = DecisionLogger()
    hazard_mask = detect_hazards(prepass)

    final_text, stats = tie_break(prepass, grammar, tts, hazard_mask, logger)

    assert final_text == "He says hello."
    assert stats["grammar"]["applied"] >= 1


def test_tie_break_preserves_title_case():
    prepass = "# Title\nAn Example"
    grammar = "# Title\nAn Example"
    tts = "# TITLE\nAn EXAMPLE"

    logger = DecisionLogger()
    hazard_mask = detect_hazards(prepass)

    final_text, stats = tie_break(prepass, grammar, tts, hazard_mask, logger)

    assert final_text.startswith("# Title")
    assert "EXAMPLE" not in final_text
    assert stats["tts"]["skipped"] >= 1


def test_postcheck_reports_hazard():
    bad_text = "Look at F ʟ ᴀ s ʜ"
    result = postcheck(bad_text)
    assert result["ok"] is False
    assert any(err["type"] == "hazard" for err in result["errors"])


def test_postcheck_ok():
    good_text = "GPU handles the workload gracefully."
    result = postcheck(good_text)
    assert result == {"ok": True, "errors": []}
*** End of File