# Commit Decoder

An autonomous agent that decodes raw git commits (message + diff) into
structured "What/How/Why" markdown reports, auto-appended to `Report.md`
and auto-committed with an `[AI-DOCS]` guardrail tag.

## Status

Day 2: two-stage LLM pipeline (skeleton extraction -> report generation)
runs end-to-end and prints the report to stdout. No Report.md writing and
no auto-commit yet, and the post-commit hook itself hasn't been built —
those land in later days.

## Requirements

- Python 3.12
- git on PATH

## Setup

```
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in the values for your provider (see
below).

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

## Running the full pipeline

`pipeline.py` extracts a commit, runs it through Stage 1 (skeleton
extraction) and Stage 2 (report generation), and prints the resulting
What/How/Why markdown report to stdout.

```
python pipeline.py            # decode HEAD
python pipeline.py <hash>     # decode a specific commit
```

By default this calls the OpenAI API (`OPENAI_API_KEY` must be set in
`.env`). On failure (bad commit, missing API key, API error) it prints
`Error: ...` to stderr and exits with status 1.

### Using a local model instead

The pipeline can run entirely against a local model through
[Ollama](https://ollama.com), instead of the OpenAI API:

1. Install Ollama and start the server: `ollama serve`
2. Pull a model, e.g.: `ollama pull qwen2.5-coder:7b`
3. In `.env`, set:
   ```
   LLM_PROVIDER=local
   LOCAL_STAGE1_MODEL=qwen2.5-coder:7b
   LOCAL_STAGE2_MODEL=qwen2.5-coder:7b
   ```
4. Run `python pipeline.py` as usual.

If Ollama isn't running, the pipeline fails fast with a clear error
telling you to start it — it won't hang or retry silently.
