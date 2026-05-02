#!/usr/bin/env python3
"""Verify generated mdBook spec integrity."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+\.md)\)")
SOURCE_RE = re.compile(r"<!--\s*source:\s*([^#]+)#L\d+(?:-L\d+)?\s+fact:\s*[0-9a-f]{12}\s*-->")


def verify_summary_links(src: Path) -> list[str]:
    errors: list[str] = []
    summary = src / "SUMMARY.md"
    if not summary.exists():
        return [f"missing {summary}"]
    for line_no, line in enumerate(summary.read_text(encoding="utf-8").splitlines(), start=1):
        for target in LINK_RE.findall(line):
            if target.startswith(("http://", "https://")):
                continue
            if not (src / target).exists():
                errors.append(f"SUMMARY.md:L{line_no} links missing page {target}")
    return errors


def verify_source_comments(src: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(src.glob("*.md")):
        if path.name in {"SUMMARY.md", "introduction.md"}:
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        bullets = [line for line in lines if line.startswith("- ")]
        if not bullets:
            errors.append(f"{path.relative_to(repo_root)} has no normative bullets")
            continue
        for line_no, line in enumerate(lines, start=1):
            if not line.startswith("- "):
                continue
            match = SOURCE_RE.search(line)
            if not match:
                errors.append(f"{path.relative_to(repo_root)}:L{line_no} missing source comment")
                continue
            source_path = repo_root / match.group(1)
            if not source_path.exists():
                errors.append(f"{path.relative_to(repo_root)}:L{line_no} references missing source {match.group(1)}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--book", type=Path, default=Path("spec"))
    args = parser.parse_args()

    repo_root = Path.cwd()
    src = args.book / "src"
    errors = verify_summary_links(src) + verify_source_comments(src, repo_root)
    if errors:
        print("spec verification failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        raise SystemExit(1)
    print("spec verification passed")


if __name__ == "__main__":
    main()
