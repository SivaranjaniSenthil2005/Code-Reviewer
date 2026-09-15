"""Mapping review findings and line numbers between diffs and full source code."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LineMapEntry:
    """Bidirectional mapping between original and normalized/diffed line numbers."""
    original_line: int
    normalized_line: int
    content: str


@dataclass
class LineMap:
    """Full bidirectional line number index for a code snippet."""
    entries: list[LineMapEntry] = field(default_factory=list)
    _orig_to_norm: dict[int, int] = field(default_factory=dict, repr=False)
    _norm_to_orig: dict[int, int] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        self._rebuild_indexes()

    def _rebuild_indexes(self):
        self._orig_to_norm = {e.original_line: e.normalized_line for e in self.entries}
        self._norm_to_orig = {e.normalized_line: e.original_line for e in self.entries}

    def original_to_normalized(self, original_line: int) -> Optional[int]:
        """Map an original source line number to its normalized equivalent."""
        return self._orig_to_norm.get(original_line)

    def normalized_to_original(self, normalized_line: int) -> Optional[int]:
        """Map a normalized line number back to the original source line."""
        return self._norm_to_orig.get(normalized_line)

    def get_context_window(self, original_line: int, window: int = 2) -> list[LineMapEntry]:
        """Return a context window of entries around an original line number."""
        return [
            e for e in self.entries
            if abs(e.original_line - original_line) <= window
        ]


def build_line_map(original_code: str, normalized_code: str) -> LineMap:
    """Build a bidirectional line number map between original and normalized code.

    Maps lines by content matching (ignoring leading/trailing whitespace).
    Unmatched lines are mapped 1:1 positionally as a fallback.
    """
    orig_lines = original_code.splitlines()
    norm_lines = normalized_code.splitlines()

    # Build a content → normalized line index for fast lookup
    norm_content_map: dict[str, list[int]] = {}
    for idx, line in enumerate(norm_lines, start=1):
        key = line.strip()
        if key:
            norm_content_map.setdefault(key, []).append(idx)

    entries: list[LineMapEntry] = []
    norm_line_usage: set[int] = set()

    for orig_idx, orig_line in enumerate(orig_lines, start=1):
        key = orig_line.strip()
        norm_line = None

        if key and key in norm_content_map:
            # Pick the first unused normalized line for this content
            candidates = norm_content_map[key]
            for candidate in candidates:
                if candidate not in norm_line_usage:
                    norm_line = candidate
                    norm_line_usage.add(candidate)
                    break

        # Positional fallback if content-match failed
        if norm_line is None:
            norm_line = orig_idx if orig_idx <= len(norm_lines) else len(norm_lines)

        entries.append(LineMapEntry(
            original_line=orig_idx,
            normalized_line=norm_line,
            content=orig_line,
        ))

    return LineMap(entries=entries)


def remap_finding_line(
    finding_line: int,
    line_map: LineMap,
    direction: str = "norm_to_orig",
) -> int:
    """Remap a finding's line number between original and normalized code.

    Args:
        finding_line: The line number reported in the finding.
        line_map: The bidirectional LineMap between original and normalized code.
        direction: Either "norm_to_orig" or "orig_to_norm".

    Returns:
        The remapped line number, or the original line number if no mapping found.
    """
    if direction == "norm_to_orig":
        remapped = line_map.normalized_to_original(finding_line)
    else:
        remapped = line_map.original_to_normalized(finding_line)

    return remapped if remapped is not None else finding_line


def remap_findings(
    findings: list[dict],
    line_map: LineMap,
    direction: str = "norm_to_orig",
) -> list[dict]:
    """Bulk-remap line numbers in a list of finding dicts.

    Each finding must have a "line" key with an integer value.
    Returns a new list of findings with remapped line numbers.
    """
    remapped = []
    for finding in findings:
        updated = dict(finding)
        if "line" in updated and isinstance(updated["line"], int):
            updated["line"] = remap_finding_line(updated["line"], line_map, direction)
        remapped.append(updated)
    return remapped
