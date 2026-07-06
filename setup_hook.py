"""
Installs the git post-commit hook that runs the Commit Decoder agent
automatically after every commit.

.git/hooks/ isn't tracked by git, so this needs to be run once after
cloning the repo:
    python setup_hook.py

Safe to re-run any time - it always overwrites .git/hooks/post-commit with
the current hook content below, rather than appending/duplicating.

Deliberately stdlib-only (no openai/dotenv import) so it can run right
after a fresh clone, before the venv/requirements are even set up.
"""

from __future__ import annotations

import stat
import subprocess
import sys
from pathlib import Path

# A POSIX shell script: Git for Windows runs hooks through its bundled sh
# via the shebang line, same as on macOS/Linux, so this one file works
# everywhere without a separate .cmd/.ps1 variant.
_HOOK_CONTENT = """\
#!/bin/sh
# Installed by setup_hook.py - runs the Commit Decoder agent after every
# commit. Do not edit directly; re-run `python setup_hook.py` instead so
# changes made here aren't silently lost on the next install.

REPO_ROOT="$(git rev-parse --show-toplevel)"
PYTHON="$REPO_ROOT/.venv/Scripts/python.exe"

if [ ! -x "$PYTHON" ]; then
    echo "[commit-decoder] Warning: venv Python not found at $PYTHON" >&2
    echo "[commit-decoder] Run: python -m venv .venv, then .venv/Scripts/pip install -r requirements.txt" >&2
    exit 0
fi

"$PYTHON" "$REPO_ROOT/run_decoder.py" HEAD
if [ $? -ne 0 ]; then
    echo "[commit-decoder] Warning: run_decoder.py reported an error (see above). Your commit itself was not affected." >&2
fi

exit 0
"""


def _repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(result.stdout.strip())


def main() -> int:
    try:
        repo_root = _repo_root()
    except FileNotFoundError:
        print("Error: git executable not found on PATH.", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError:
        print("Error: not inside a git repository.", file=sys.stderr)
        return 1

    hooks_dir = repo_root / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path = hooks_dir / "post-commit"

    # newline="\n" is load-bearing: without it, Python would translate \n
    # to \r\n on Windows, and a CRLF shebang line breaks git bash's sh.
    hook_path.write_text(_HOOK_CONTENT, encoding="utf-8", newline="\n")

    mode = hook_path.stat().st_mode
    hook_path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    print(f"Installed post-commit hook at {hook_path}")
    print("The Commit Decoder agent will now run automatically after every commit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
