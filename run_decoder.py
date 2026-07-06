"""
Day 3: end-to-end run - extract a commit, run it through the two-stage LLM
pipeline, top-append the result to Report.md, and auto-commit that file
with an [AI-DOCS] tag.

Skips entirely (no LLM calls, no writes, no commit) if the target commit's
message already carries the AI_DOCS_PREFIX - see pipeline.run(). That
guardrail is what stops a post-commit hook (wired up next session) from
re-triggering on its own auto-committed Report.md updates.

Run manually for now:
    python run_decoder.py [hash]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from llm_client import LLMConfigError
from pipeline import AI_DOCS_PREFIX, PipelineError
from pipeline import run as run_pipeline
from report_writer import top_append_entry

REPORT_PATH = Path("Report.md")


def _commit_report(short_hash: str) -> None:
    """Stage and commit Report.md.

    Failures here are logged, not raised: Report.md was already written
    successfully to disk by this point, so a git error (nothing to commit,
    hook rejection, etc.) shouldn't be treated as a fatal script failure.
    """
    try:
        subprocess.run(
            ["git", "add", "Report.md"],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "commit", "-m", f"{AI_DOCS_PREFIX} {short_hash}"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        print(
            f"Warning: Report.md was updated but the auto-commit failed: "
            f"{stderr or exc}",
            file=sys.stderr,
        )
        return

    print(f"Committed Report.md as '{AI_DOCS_PREFIX} {short_hash}'.")


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Decode a commit into Report.md and auto-commit it."
    )
    parser.add_argument(
        "revision",
        nargs="?",
        default="HEAD",
        help="Commit hash or revision to decode (default: HEAD)",
    )
    args = parser.parse_args(argv)

    try:
        result = run_pipeline(args.revision)
    except (PipelineError, LLMConfigError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if result is None:
        print(
            f"Skipped: commit message already has an {AI_DOCS_PREFIX} prefix.",
        )
        return 0

    commit, entry = result

    try:
        top_append_entry(REPORT_PATH, entry)
    except OSError as exc:
        print(f"Error: failed to write {REPORT_PATH}: {exc}", file=sys.stderr)
        return 1

    short_hash = commit.commit_hash[:7]
    print(f"Report.md updated for commit #{short_hash}.")
    _commit_report(short_hash)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
