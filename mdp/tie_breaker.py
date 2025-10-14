"""Phase 12 tie-breaker and postcheck utilities.

Provides deterministic merge between prepass, grammar, and TTS-fixer outputs
while enforcing TTS safety hazards and Markdown integrity.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
import json
import unicodedata
import re
from difflib import SequenceMatcher


@dataclass
class HazardSpan:
    """Represents a span of text that should remain untouched by later stages."""

    start: int
    end: int
    reason: str

    def to_dict(self) -> dict:
        return {"start": self.start, "end": self.end, "reason": self.reason}


@dataclass
class Decision:
    """Records a single tie-breaker decision."""

    stage: str
    rule: str
    before: str
    after: str
    span: Tuple[int, int]
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        record = {
            "stage": self.stage,
            "rule": self.rule,
            "before": self.before,
            "after": self.after,
            "span": list(self.span),
        }
        if self.metadata:
            record["metadata"] = self.metadata
        return record


class DecisionLogger:
    """Append-only NDJSON logger for tie-breaker decisions."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path
        self.counts = {"grammar": {"applied": 0, "skipped": 0}, "tts": {"applied": 0, "skipped": 0}}
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.touch(exist_ok=True)

    def log(self, decision: Decision) -> None:
        stage_key = "tts" if decision.stage.startswith("tts") else "grammar"
        if decision.rule == "apply":
            self.counts.setdefault(stage_key, {}).setdefault("applied", 0)
            self.counts[stage_key]["applied"] += 1
        else:
            self.counts.setdefault(stage_key, {}).setdefault("skipped", 0)
            self.counts[stage_key]["skipped"] += 1

        if not self.path:
            return

        record = json.dumps(decision.to_dict(), ensure_ascii=False)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(record + "\n")

    def summary(self) -> dict:
        return self.counts


_SPACED_PATTERN = re.compile(r"(?iu)\b\w(?:[\s,\-]\w){3,}\b")
_UPPER_PATTERN = re.compile(r"\b[A-Z]{6,}\b")

_ACRONYM_WHITELIST: set[str] = set()


def set_acronym_whitelist(items: Iterable[str]) -> None:
    """Update the in-memory whitelist for acronym preservation."""
    global _ACRONYM_WHITELIST
    _ACRONYM_WHITELIST = {item.strip().upper() for item in items if item and item.strip()}


def _is_stylized(char: str) -> bool:
    if not char:
        return False
    code_point = ord(char)
    if 0x1D00 <= code_point <= 0x1D7F:
        return True  # phonetic extensions/small capitals
    if 0x1D80 <= code_point <= 0x1DBF:
        return True
    if 0x1E00 <= code_point <= 0x1EFF:
        return True
    category = unicodedata.category(char)
    if category in {"Lm", "Sk"}:
        return True
    try:
        name = unicodedata.name(char)
    except ValueError:
        return False
    return "SMALL CAPITAL" in name or "MODIFIER LETTER" in name


def detect_hazards(text: str, acronyms: Optional[Iterable[str]] = None) -> List[HazardSpan]:
    """Return hazard spans (by index) detected in *text*.

    Hazards include spaced letters, stylized Unicode, and long all-caps words
    that could harm TTS output.
    """
    if not text:
        return []

    if acronyms is None:
        whitelist = _ACRONYM_WHITELIST
    else:
        whitelist = {item.strip().upper() for item in acronyms if item and item.strip()}

    spans: List[HazardSpan] = []

    for match in _SPACED_PATTERN.finditer(text):
        spans.append(HazardSpan(match.start(), match.end(), "spaced_letters"))

    for match in _UPPER_PATTERN.finditer(text):
        token = match.group(0).upper()
        if whitelist and token in whitelist:
            continue
        spans.append(HazardSpan(match.start(), match.end(), "uppercase_non_acronym"))

    index = 0
    while index < len(text):
        char = text[index]
        if _is_stylized(char):
            start = index
            while index < len(text) and _is_stylized(text[index]):
                index += 1
            spans.append(HazardSpan(start, index, "stylized_unicode"))
            continue
        index += 1

    # Merge overlapping spans to simplify downstream consumers
    merged: List[HazardSpan] = []
    for span in sorted(spans, key=lambda s: (s.start, s.end)):
        if not merged:
            merged.append(span)
            continue
        last = merged[-1]
        if span.start <= last.end:
            merged[-1] = HazardSpan(last.start, max(last.end, span.end), last.reason)
        else:
            merged.append(span)
    return merged


def _intersects_mask(i1: int, i2: int, mask: List[HazardSpan]) -> bool:
    return any(not (i2 <= span.start or i1 >= span.end) for span in mask)


def _shift_mask(mask: List[HazardSpan], pivot: int, delta: int) -> None:
    if delta == 0:
        return
    for span in mask:
        if span.start >= pivot:
            span.start += delta
            span.end += delta


def _should_skip(before: str, after: str, stage: str, acronyms: Optional[Iterable[str]]) -> Optional[str]:
    if not after:
        return None
    if detect_hazards(after, acronyms):
        return "hazard_detected"
    stripped_before = before.strip()
    if stage.startswith("tts") and stripped_before.isupper():
        if acronyms is None:
            whitelist = _ACRONYM_WHITELIST
        else:
            whitelist = {item.strip().upper() for item in acronyms if item and item.strip()}
        if whitelist and stripped_before.upper() in whitelist:
            return "preserve_acronym"
        if len(stripped_before) <= 5 and not after.isupper():
            return "preserve_acronym"
    return None


def _merge_stage(
    base_text: str,
    target_text: str,
    stage: str,
    mask: List[HazardSpan],
    logger: DecisionLogger,
    stage_metadata: Optional[dict] = None,
    acronyms: Optional[Iterable[str]] = None,
) -> Tuple[str, List[HazardSpan], dict]:
    if target_text is None or target_text == base_text:
        return base_text, mask, {"applied": 0, "skipped": 0}

    matcher = SequenceMatcher(None, base_text, target_text)
    result_segments: List[str] = []
    cursor = 0
    stats = {"applied": 0, "skipped": 0}

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if cursor < i1:
            result_segments.append(base_text[cursor:i1])
        if tag == "equal":
            result_segments.append(base_text[i1:i2])
        else:
            before = base_text[i1:i2]
            after = target_text[j1:j2]
            skip_reason: Optional[str] = None
            if _intersects_mask(i1, i2, mask):
                skip_reason = "protected_span"
            else:
                skip_reason = _should_skip(before, after, stage, acronyms)

            if skip_reason:
                result_segments.append(before)
                stats["skipped"] += 1
                logger.log(
                    Decision(
                        stage=stage,
                        rule=f"skip:{skip_reason}",
                        before=before,
                        after=after,
                        span=(i1, i2),
                        metadata=stage_metadata,
                    )
                )
            else:
                result_segments.append(after)
                stats["applied"] += 1
                logger.log(
                    Decision(
                        stage=stage,
                        rule="apply",
                        before=before,
                        after=after,
                        span=(i1, i2),
                        metadata=stage_metadata,
                    )
                )
                delta = len(after) - len(before)
                if delta:
                    _shift_mask(mask, i2, delta)
        cursor = i2
    if cursor < len(base_text):
        result_segments.append(base_text[cursor:])

    merged_text = "".join(result_segments)
    return merged_text, mask, stats


def tie_break(
    prepass_text: str,
    grammar_text: Optional[str],
    tts_text: Optional[str],
    hazard_mask: List[HazardSpan],
    logger: Optional[DecisionLogger] = None,
    stage_metadata: Optional[Dict[str, dict]] = None,
    acronym_whitelist: Optional[Iterable[str]] = None,
) -> Tuple[str, dict]:
    """Perform deterministic merge honoring stage priority.

    Returns the merged text and a stats dictionary summarizing applied/skipped edits.
    """
    logger = logger or DecisionLogger()
    mask_copy = [HazardSpan(span.start, span.end, span.reason) for span in hazard_mask]
    stats_summary = {"grammar": {"applied": 0, "skipped": 0}, "tts": {"applied": 0, "skipped": 0}}

    current_text = prepass_text or ""

    metadata = stage_metadata or {}
    if grammar_text is not None:
        current_text, mask_copy, grammar_stats = _merge_stage(
            current_text,
            grammar_text,
            "grammar",
            mask_copy,
            logger,
            metadata.get("grammar"),
            acronym_whitelist,
        )
        stats_summary["grammar"] = grammar_stats

    if tts_text is not None:
        current_text, mask_copy, tts_stats = _merge_stage(
            current_text,
            tts_text,
            "tts-fixer",
            mask_copy,
            logger,
            metadata.get("fixer"),
            acronym_whitelist,
        )
        stats_summary["tts"] = tts_stats

    stats_summary["hazard_spans_protected"] = len(hazard_mask)
    stats_summary["logger"] = logger.summary()
    return current_text, stats_summary


def _check_backticks(text: str) -> Optional[str]:
    if text.count("```") % 2 != 0:
        return "unbalanced_code_fences"
    return None


def _check_brackets(text: str) -> Optional[str]:
    stack = []
    pairs = {"[": "]", "(": ")", "{": "}"}
    closing = {v: k for k, v in pairs.items()}
    for char in text:
        if char in pairs:
            stack.append(char)
        elif char in closing:
            if not stack or stack[-1] != closing[char]:
                return "unbalanced_brackets"
            stack.pop()
    if stack:
        return "unbalanced_brackets"
    return None


def postcheck(text: str, acronym_whitelist: Optional[Iterable[str]] = None) -> dict:
    """Validate final text for hazards and basic Markdown integrity."""
    errors = []
    hazards = detect_hazards(text, acronym_whitelist)
    if hazards:
        errors.append({"type": "hazard", "spans": [span.to_dict() for span in hazards]})

    fence_issue = _check_backticks(text)
    if fence_issue:
        errors.append({"type": fence_issue})

    bracket_issue = _check_brackets(text)
    if bracket_issue:
        errors.append({"type": bracket_issue})

    return {"ok": not errors, "errors": errors}