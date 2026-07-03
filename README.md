# Commit Decoder

An autonomous agent that decodes raw git commits (message + diff) into
structured "What/How/Why" markdown reports, auto-appended to `Report.md`
and auto-committed with an `[AI-DOCS]` guardrail tag.

## Status

Day 1: commit extraction utility only. No LLM calls yet, no post-commit
hook yet — those land in later days.

## Requirements

- Python 3.14
- git on PATH

## Setup

```
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

(No third-party dependencies yet — `requirements.txt` is a placeholder for
the LLM SDKs that later days will add.)

## Running the extractor standalone

`extract_commit.py` reads a single commit (default: `HEAD`) via `git show`
and prints it as JSON: `commit_hash`, `author`, `timestamp`, `message`,
and the raw `diff` text.

```
python extract_commit.py            # extract HEAD
python extract_commit.py <hash>     # extract a specific commit
```

Example output:

```json
{
  "commit_hash": "a1b2c3d4e5f6...",
  "author": "Jane Doe <jane@example.com>",
  "timestamp": "2026-07-03T14:02:11-07:00",
  "message": "Fix off-by-one in pagination",
  "diff": "diff --git a/foo.py b/foo.py\n..."
}
```

On failure (bad hash, repo has no commits yet, not a git repo) it prints
`{"error": "..."}` to stderr and exits with status 1.
