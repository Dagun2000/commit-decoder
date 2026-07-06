# Commit Decoder

An autonomous agent that decodes raw git commits (message + diff) into
structured "What/How/Why" markdown reports, auto-appended to `Report.md`
and auto-committed with an `[AI-DOCS]` guardrail tag.

## Example Output
--------------------------------------------------------------------------------------------------------------

## [2026-07-06 09:07] Commit: #9f8c1f1
* **Author:** Dagun2000
* **Original Message:** `Added pipeline and actual llm`

### 1. What (기능적 요약)
이번 변경은 커밋 분석 도구에 실제 LLM 연동과 end-to-end 파이프라인 실행 기능을 추가한 것이다. 이제 원본 커밋 정보에서 Stage 1 스켈레톤을 추출하고, 이를 바탕으로 Stage 2 한국어 분석 리포트를 생성하는 전체 흐름이 동작한다. 또한 OpenAI와 로컬 Ollama를 선택적으로 사용할 수 있도록 구성되었고, 실행 방법과 환경 설정이 README에 반영되었다.

### 2. How (구현 메커니즘)
`llm_client.py`에 LLM 설정 객체와 설정 오류 처리, 그리고 provider별 클라이언트 생성 로직이 추가되어 환경변수 기반으로 OpenAI/Ollama를 전환한다. `stage1_skeleton.py`는 raw diff를 구조화된 스켈레톤으로 압축하는 전용 프롬프트와 chat-completions 호출을 담당하고, `stage2_report.py`는 이 스켈레톤을 입력으로 최종 분석 문서를 생성하며 빈 스켈레톤일 때는 조기 종료한다. `pipeline.py`는 `extract_commit -> stage1_skeleton -> stage2_report` 순서로 전체 단계를 오케스트레이션하고, 결과를 포맷팅해 출력하는 CLI 진입점 역할을 한다.

### 3. Why (기술적 의도)
핵심 의도는 기존의 플레이스홀더 수준 구현을 실제 사용 가능한 LLM 기반 분석 파이프라인으로 전환하는 데 있다. Stage 1에서 diff를 먼저 압축해 노이즈를 줄임으로써 Stage 2가 더 안정적으로 의도와 구조를 해석하도록 설계한 것으로 보인다. 또한 클라우드 API와 로컬 모델을 모두 지원해 개발 편의성, 비용 통제, 오프라인 실험 가능성을 함께 확보하려는 목적이 반영되어 있다.

---

--------------------------------------------------------------------------------------------------------------

## Status

Day 4: the full pipeline (extract -> Stage 1 -> Stage 2 -> top-append to
Report.md -> auto-commit with `[AI-DOCS]`) is wired into a git post-commit
hook and runs automatically after every commit.

## Requirements

- Python 3.12
- git on PATH

## Setup

```
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in the values for your provider (see
below).

Then, once per clone, install the git hook so the agent runs automatically
after every commit:

```
python setup_hook.py
```

`.git/hooks/` isn't tracked by git, so this is a one-time manual step after
cloning (or after moving the repo to a new machine). It's safe to re-run
any time - it always overwrites the hook cleanly rather than duplicating
it.

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

### Choosing the report language

By default the What/How/Why report is written in Korean. To get English
output instead, set in `.env`:

```
REPORT_LANGUAGE=en
```

Valid values are `ko` (default) and `en`. This applies to both the OpenAI
and local providers, and to the `[AI-DOCS]` reports auto-committed by the
post-commit hook.

## Automatic decoding on every commit

Once `setup_hook.py` has been run, every `git commit` automatically
triggers `run_decoder.py HEAD` afterward, which:

1. Skips entirely (no API calls, no writes) if the commit's message
   already has an `[AI-DOCS]` prefix - this is what stops the hook from
   re-triggering on its own auto-commits
2. Otherwise runs the full pipeline and top-appends the resulting entry to
   `Report.md` (newest first)
3. Commits `Report.md` with the message `[AI-DOCS] <short-hash>`

This never blocks or fails your actual commit - if the decoder script hits
an error, it prints a warning and the hook still exits 0.

`run_decoder.py [hash]` can also be run by hand (default: `HEAD`), which is
useful for decoding a commit made before the hook was installed.
