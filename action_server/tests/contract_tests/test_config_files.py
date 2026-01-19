"""
Contract tests for configuration file constraints (T026a).

Validates NFR-007: tier-selection/configuration logic must be confined to a
small, well-known set of configuration files to avoid sprawl of tier logic
across the codebase. This test scans the repository for common "tier" patterns
and fails if those patterns are detected outside the allowed configuration
files.

The allowed files (authoritative sources of tier logic) are:
  - action_server/build-binary/tier_selector.py
  - action_server/frontend/vite.config.js
  - action_server/frontend/feature-boundaries.json

Note: This test intentionally scans code files only (Python, JS/TS, JSON, YAML)
and excludes specs, tests, docs and vendored/build artifacts to reduce noise.
"""

import re
from pathlib import Path

# Patterns that indicate presence of tier selection / tier-specific logic.
# These are intentionally conservative (look for assignment, env var access,
# comparisons or explicit select_tier calls) to avoid false positives from
# innocuous uses of the words "community" or "enterprise" in documentation.
PATTERNS = [
    re.compile(r"\bselect_tier\s*\(") ,
    re.compile(r"os\.environ\[['\"]TIER['\"]\]"),
    re.compile(r"os\.environ\.get\(\s*['\"]TIER['\"]\s*\)"),
    re.compile(r"process\.env\.TIER"),
    # bracket-access form: process.env['TIER'] or process.env["TIER"]
    re.compile(r"process\.env\[\s*['\"]TIER['\"]\s*\]"),
    re.compile(r"__TIER__"),
    re.compile(r"\btier\s*(?:===|==|:=|=)\s*['\"](?:community|enterprise)['\"]", re.IGNORECASE),
    re.compile(r"\bTierName\.(?:COMMUNITY|ENTERPRISE)\b"),
    re.compile(r"\b(tier_name|tier)\s*(?:===|==)\s*['\"](?:community|enterprise)['\"]", re.IGNORECASE),
]


def _is_excluded(path: Path, excluded_dirs):
    for part in path.parts:
        if part in excluded_dirs:
            return True
    return False


def find_tier_logic_files(repo_root: Path):
    """Scan the repository for files that contain tier-selection patterns.

    Returns a set of repository-relative POSIX paths for matched files.
    """
    include_exts = {".py", ".js", ".ts", ".tsx", ".json", ".yml", ".yaml"}
    excluded_dirs = {
        "specs",
        "tests",
        ".git",
        "node_modules",
        "dist",
        "build",
    "vendored",
        "action_server/dist",
        "action_server/frontend/dist",
        "action_server/frontend/node_modules",
    }

    found = set()

    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue

        if _is_excluded(path, excluded_dirs):
            continue

        if path.suffix not in include_exts:
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            # Ignore files that can't be decoded as UTF-8
            continue

        for pat in PATTERNS:
            if pat.search(content):
                found.add(path.relative_to(repo_root).as_posix())
                break

    return found


def test_tier_logic_confined_to_config_files():
    """Assert that tier-selection logic is confined to the approved config files.

    If any unexpected files contain tier-selection patterns, the test fails and
    lists the offending files to help remediate the sprawl.
    """
    repo_root = Path(__file__).resolve().parents[3]

    found = find_tier_logic_files(repo_root)

    # Authoritative locations where tier selection/configuration logic is allowed
    allowed = {
        "action_server/build-binary/tier_selector.py",
        "action_server/frontend/vite.config.js",
        "action_server/frontend/feature-boundaries.json",
    }

    # Sanity check: ensure the allowed files exist (if not, the test should
    # still surface other violations but indicate missing authoritative files).
    missing_allowed = [p for p in allowed if not (repo_root / p).exists()]
    assert not missing_allowed, (
        "Expected allowed config files to exist but they are missing: "
        f"{missing_allowed}")

    unexpected = sorted(found - allowed)

    assert not unexpected, (
        "Tier-selection/configuration logic detected outside of the approved "
        "configuration files. Move tier logic into one of: "
        f"{sorted(allowed)}. Offending files:\n  " + "\n  ".join(unexpected)
    )
