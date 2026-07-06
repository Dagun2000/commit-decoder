"""
Stage 1: the "token diet" step.

Takes a raw unified diff and asks a lightweight model to compress it down
to a skeleton - the substantive structural changes only (functions,
methods, classes, variables touched), with comments, whitespace-only
diffs, and typo fixes stripped out. Stage 2 reads this skeleton instead of
the full diff.
"""

from __future__ import annotations

from openai import OpenAI

_SYSTEM_PROMPT = """\
You compress a raw git diff into a compact structural skeleton for a \
downstream model that will never see the original diff.

Output only:
- Changed functions, methods, classes, and variables (qualified by file \
where useful), and a short note of what structurally changed for each \
(added / removed / signature changed / logic changed / moved).

Strip out entirely:
- Comment-only changes
- Whitespace/formatting-only changes
- Typo fixes in strings or comments
- Import reordering with no new/removed imports

Do not include full code bodies. Do not add commentary, headers, or \
markdown formatting - plain terse lines only. If a file's changes are \
entirely noise (comments/whitespace/typos), omit that file.
"""


def extract_skeleton(diff_text: str, client: OpenAI, model: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": diff_text},
        ],
        temperature=0,
    )
    return response.choices[0].message.content.strip()
