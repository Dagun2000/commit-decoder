"""
Day 2: chains Day 1's commit extraction through the two-stage LLM pipeline
and prints the generated What/How/Why markdown report to stdout.

No file writing or git commit yet - Report.md updates and the auto-commit
land in a later session.
"""

from __future__ import annotations

import argparse
import datetime
import sys

from openai import APIConnectionError, OpenAIError

from extract_commit import CommitExtractionError, CommitRecord, extract_commit
from llm_client import LLMConfig, LLMConfigError, get_llm_client
from stage1_skeleton import extract_skeleton
from stage2_report import generate_report

_SHORT_HASH_LENGTH = 7
AI_DOCS_PREFIX = "[AI-DOCS]"


class PipelineError(Exception):
    """Raised when a pipeline stage fails; carries a user-facing message."""


def _connection_hint(config: LLMConfig) -> str:
    if config.provider == "local":
        return (
            "Could not reach the local LLM server at the configured "
            "OLLAMA_BASE_URL. Is Ollama running? Start it with "
            "`ollama serve` and make sure the model has been pulled."
        )
    return "Could not reach the OpenAI API. Check your network connection."


def format_report_entry(commit: CommitRecord, body: str) -> str:
    """Prefix the LLM-generated What/How/Why body with a deterministic
    header (timestamp, short hash, author, original message) built purely
    from extracted commit metadata - not the LLM - so it's never subject to
    hallucination.
    """
    timestamp = datetime.datetime.fromisoformat(commit.timestamp)
    short_hash = commit.commit_hash[:_SHORT_HASH_LENGTH]
    subject = commit.message.splitlines()[0] if commit.message else ""
    author_name = commit.author.split(" <", 1)[0]

    header = (
        f"## [{timestamp:%Y-%m-%d %H:%M}] Commit: #{short_hash}\n"
        f"* **Author:** {author_name}\n"
        f"* **Original Message:** `{subject}`\n"
    )
    return f"{header}\n{body.strip()}\n\n---\n"


def run(revision: str) -> tuple[CommitRecord, str] | None:
    """Run the full extract -> Stage 1 -> Stage 2 pipeline for a commit.

    Returns None (skipping all LLM calls) if the commit's message already
    carries the AI_DOCS_PREFIX - that's the guardrail against the agent
    re-processing its own auto-committed Report.md updates.
    """
    try:
        commit = extract_commit(revision)
    except CommitExtractionError as exc:
        raise PipelineError(f"Commit extraction failed: {exc}") from exc

    if commit.message.startswith(AI_DOCS_PREFIX):
        return None

    config = get_llm_client()

    try:
        skeleton = extract_skeleton(commit.diff, config.client, config.stage1_model)
    except APIConnectionError as exc:
        raise PipelineError(_connection_hint(config)) from exc
    except OpenAIError as exc:
        raise PipelineError(f"Stage 1 (skeleton extraction) failed: {exc}") from exc

    try:
        body = generate_report(
            skeleton, commit.message, config.client, config.stage2_model
        )
    except APIConnectionError as exc:
        raise PipelineError(_connection_hint(config)) from exc
    except OpenAIError as exc:
        raise PipelineError(f"Stage 2 (report generation) failed: {exc}") from exc

    return commit, format_report_entry(commit, body)


def main(argv: list[str] | None = None) -> int:
    # Windows' console codepage is often not UTF-8, which otherwise silently
    # mangles the Korean report text on print() (and on file redirection).
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Generate a What/How/Why report for a git commit."
    )
    parser.add_argument(
        "revision",
        nargs="?",
        default="HEAD",
        help="Commit hash or revision to decode (default: HEAD)",
    )
    args = parser.parse_args(argv)

    try:
        result = run(args.revision)
    except (PipelineError, LLMConfigError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if result is None:
        print(
            f"Skipped: commit message already has an {AI_DOCS_PREFIX} prefix.",
            file=sys.stderr,
        )
        return 0

    _commit, entry = result
    print(entry)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
