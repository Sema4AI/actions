#!/usr/bin/env python3
"""Standalone verification script for T026a test logic."""
from pathlib import Path
import re

PATTERNS = [
    re.compile(r"\bselect_tier\s*\("),
    re.compile(r"os\.environ\[['\"]TIER['\"]\]"),
    re.compile(r"os\.environ\.get\(\s*['\"]TIER['\"]\s*\)"),
    re.compile(r"process\.env\.TIER"),
    re.compile(r"__TIER__"),
    re.compile(r"\btier\s*(?:===|==|:=|=)\s*['\"](?:community|enterprise)['\"]", re.IGNORECASE),
    re.compile(r"\bTierName\.(?:COMMUNITY|ENTERPRISE)\b"),
    re.compile(r"\b(tier_name|tier)\s*(?:===|==)\s*['\"](?:community|enterprise)['\"]", re.IGNORECASE),
]

def _is_excluded(path, excluded_dirs):
    for part in path.parts:
        if part in excluded_dirs:
            return True
    return False

repo_root = Path(".")
include_exts = {".py", ".js", ".ts", ".tsx", ".json", ".yml", ".yaml"}
excluded_dirs = {
    "specs", "tests", ".git", "node_modules", "dist", "build", "vendor",
    "action_server/dist", "action_server/frontend/dist", "action_server/frontend/node_modules",
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
        continue
    for pat in PATTERNS:
        if pat.search(content):
            found.add(path.relative_to(repo_root).as_posix())
            break

allowed = {
    "action_server/build-binary/tier_selector.py",
    "action_server/frontend/vite.config.js",
    "action_server/frontend/feature-boundaries.json",
}

unexpected = sorted(found - allowed)
print(f"Found {len(found)} files with tier logic patterns")
print(f"Allowed files: {sorted(allowed)}")
print(f"\nUnexpected files ({len(unexpected)}):")
for f in unexpected[:30]:
    print(f"  - {f}")
if len(unexpected) > 30:
    print(f"  ... and {len(unexpected) - 30} more")
