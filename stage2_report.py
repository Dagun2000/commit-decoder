"""
Stage 2: takes the Stage 1 skeleton + original commit message and infers
technical intent and architecture, producing the final What/How/Why
markdown report in the exact Report.md section format.
"""

from __future__ import annotations

from openai import OpenAI

# Stage 1 returns an empty string when every changed file was pure noise
# (comments/whitespace/typos) - see stage1_skeleton.py. Rather than trust
# the model to notice "nothing to analyze" every time (small local models
# especially may not), we short-circuit deterministically and skip the
# Stage 2 call entirely for that case.
_NO_SUBSTANTIVE_CHANGES_BODY = """\
### 1. What (기능적 요약)
이 커밋은 주석, 공백, 오타 수정 등 비기능적 변경만 포함하고 있어 실질적인 코드 동작 변화가 없습니다.

### 2. How (구현 메커니즘)
Stage 1 분석 결과 구조적으로 변경된 함수, 클래스, 변수가 없어 별도의 구현 메커니즘이 존재하지 않습니다.

### 3. Why (기술적 의도)
가독성 개선이나 문서 정리 등 비기능적 목적의 변경으로 추정됩니다.\
"""

_SYSTEM_PROMPT = """\
You are a senior engineer writing a commit analysis report in Korean.

You are given the original commit message and a Stage 1 skeleton (changed \
functions/classes/variables with noise already stripped out - you will \
not see the raw diff). Infer the technical intent and architecture behind \
the change from these two inputs.

Output markdown with EXACTLY these three sections, in this exact order, \
using these exact headings and nothing else before, between, or after them:


### 1. What (기능적 요약)
### 2. How (구현 메커니즘)
### 3. Why (기술적 의도)

Write all section content in Korean, 2-5 concise sentences each. Do not \
add extra sections, a title, or any preamble/postamble text.
"""


def generate_report(
    skeleton: str, commit_message: str, client: OpenAI, model: str
) -> str:
    if not skeleton.strip():
        return _NO_SUBSTANTIVE_CHANGES_BODY

    user_content = (
        f"Original commit message:\n{commit_message}\n\n"
        f"Stage 1 skeleton:\n{skeleton}"
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()
