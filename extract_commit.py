"""
Extracts a single git commit (metadata + diff) into a structured record.

Day 1 of the Commit Decoder pipeline: this module has no LLM dependency.
It only shells out to `git show` and parses the result into a CommitRecord
that later pipeline stages can consume.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import subprocess
import sys

# ASCII unit separator: used as a field delimiter in the `git show` format
# string below, since it's control-plane and won't appear in real commit
# metadata (unlike commas, pipes, or colons).
_FIELD_SEP = "\x1f"
_METADATA_FORMAT = f"%H{_FIELD_SEP}%an <%ae>{_FIELD_SEP}%aI{_FIELD_SEP}%B"


class CommitExtractionError(Exception):
    """Raised when a commit cannot be resolved or read from the repo."""


@dataclasses.dataclass
class CommitRecord:
    commit_hash: str
    author: str
    timestamp: str  # ISO 8601, e.g. 2026-07-03T14:02:11-07:00
    message: str
    diff: str

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def _run_git(args: list[str]) -> str:
    """Run a git command and return decoded stdout.

    Non-UTF8 bytes (rare, but possible in binary diffs or legacy commit
    messages) are replaced rather than raising, so a single malformed byte
    never takes down the whole extraction.
    """
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
    except FileNotFoundError as exc:
        raise CommitExtractionError("git executable not found on PATH") from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise CommitExtractionError(stderr or f"git {' '.join(args)} failed") from exc
    return result.stdout


def _resolve_commit_hash(revision: str) -> str:
    """Resolve a revision (HEAD, short hash, etc.) to a full commit hash.

    Resolving first and reusing the resolved hash for later commands avoids
    ever passing user-controlled input straight into a second `git show`
    call, and gives a clean, specific error for empty repos or bad hashes
    instead of a raw CalledProcessError.
    """
    try:
        output = _run_git(["rev-parse", "--verify", f"{revision}^{{commit}}"])
    except CommitExtractionError as exc:
        message = str(exc).lower()
        unresolved_markers = (
            "unknown revision",
            "bad revision",
            "needed a single revision",
            "ambiguous argument",
        )
        if any(marker in message for marker in unresolved_markers):
            raise CommitExtractionError(
                f"'{revision}' does not resolve to a commit "
                "(does this repo have any commits yet?)"
            ) from exc
        raise
    return output.strip()


def extract_commit(revision: str = "HEAD") -> CommitRecord:
    """Extract metadata + diff for a single commit as a CommitRecord."""
    commit_hash = _resolve_commit_hash(revision)

    metadata_raw = _run_git(["show", "-s", f"--format={_METADATA_FORMAT}", commit_hash])
    parts = metadata_raw.split(_FIELD_SEP, 3)
    if len(parts) != 4:
        raise CommitExtractionError(
            f"unexpected metadata format for commit {commit_hash}"
        )
    _hash, author, timestamp, message = parts

    diff = _run_git(["show", "-U3", "--no-color", "--format=", commit_hash])
    diff = diff.lstrip("\n")

    return CommitRecord(
        commit_hash=commit_hash,
        author=author.strip(),
        timestamp=timestamp.strip(),
        message=message.strip("\n"),
        diff=diff,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract a git commit's metadata and diff as JSON."
    )
    parser.add_argument(
        "revision",
        nargs="?",
        default="HEAD",
        help="Commit hash or revision to extract (default: HEAD)",
    )
    args = parser.parse_args(argv)

    try:
        record = extract_commit(args.revision)
    except CommitExtractionError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1

    print(json.dumps(record.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
