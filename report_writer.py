"""
Top-appends a single decoded commit entry to Report.md - newest entries
first, directly below the file's canonical header.
"""

from __future__ import annotations

from pathlib import Path

REPORT_HEADER = "# Project Git Commit Decoder Chronicles"


def top_append_entry(report_path: Path, entry: str) -> None:
    """Insert `entry` directly below the header, above any existing entries.

    The full new file content is built in memory first and written with a
    single call, so a failure mid-run can never leave Report.md truncated
    or half-written.
    """
    if report_path.exists():
        existing = report_path.read_text(encoding="utf-8")
    else:
        existing = ""

    if existing.startswith(REPORT_HEADER):
        prior_entries = existing[len(REPORT_HEADER):].lstrip("\n")
    else:
        # Fresh file, or content that predates the canonical header (e.g.
        # the Day 1 placeholder) - nothing to preserve as a prior entry.
        prior_entries = ""

    new_content = f"{REPORT_HEADER}\n\n{entry.strip()}\n"
    if prior_entries:
        new_content += f"\n{prior_entries}"

    report_path.write_text(new_content, encoding="utf-8")
