#!/usr/bin/env python3
"""
Verifies that every file path and test reference cited in TRACEABILITY_MATRIX.md
actually exists in the repository. Fails the build (non-zero exit) if any cited
backend file, frontend screen, script, doc, or `tests/x.py::test_name` reference
is stale — the exact rot this document exists to prevent.

Usage:
    python scripts/verify_traceability.py

Convention this script relies on: every verifiable citation in the matrix is
written inside backtick code spans (`like/this.py` or `tests/file.py::test_name`)
and starts with one of the recognized repo-root prefixes below. Prose backticked
for other reasons (e.g. `flag_name`, `ENV_VAR`) is intentionally ignored because
it does not start with a repo-root prefix.
"""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MATRIX_PATH = REPO_ROOT / "TRACEABILITY_MATRIX.md"

# Only tokens starting with one of these are treated as verifiable path claims.
PATH_PREFIXES = ("backend/", "frontend/", "tests/", "scripts/", "docs/", "alembic/", ".github/")

BACKTICK_SPAN = re.compile(r"`([^`]+)`")
TEST_FUNC_PATTERN = "def {name}("


def _find_test_function(file_path: Path, func_name: str) -> bool:
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError:
        return False
    return TEST_FUNC_PATTERN.format(name=func_name) in content


def verify() -> int:
    if not MATRIX_PATH.exists():
        print(f"FAIL: {MATRIX_PATH} does not exist.")
        return 1

    text = MATRIX_PATH.read_text(encoding="utf-8")
    tokens = sorted(set(BACKTICK_SPAN.findall(text)))

    errors = []
    checked = 0

    for token in tokens:
        # A cell can list multiple citations separated by whitespace/newlines inside
        # one backtick span in rare cases; split defensively on whitespace.
        for candidate in token.split():
            candidate = candidate.strip().rstrip(",;")
            if not candidate.startswith(PATH_PREFIXES):
                continue
            checked += 1

            if "::" in candidate:
                file_part, func_part = candidate.split("::", 1)
            else:
                file_part, func_part = candidate, None

            file_path = REPO_ROOT / file_part
            if not file_path.exists():
                errors.append(f"Missing path: `{candidate}` (resolved: {file_path})")
                continue

            if func_part:
                if not _find_test_function(file_path, func_part):
                    errors.append(f"Missing test function `{func_part}` in {file_part}")

    print(f"Checked {checked} citation(s) from {MATRIX_PATH.relative_to(REPO_ROOT)}.")

    if errors:
        print(f"\nFAIL: {len(errors)} stale traceability citation(s) found:\n")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASS: All traceability citations resolve to real files/tests.")
    return 0


if __name__ == "__main__":
    sys.exit(verify())
