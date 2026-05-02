#!/usr/bin/env python3
"""Verify generated mdBook spec integrity."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+\.md)\)")
SOURCE_RE = re.compile(r"<!--\s*source:\s*([^#]+)#L\d+(?:-L\d+)?\s+fact:\s*[0-9a-f]{12}\s*-->")
REQ_RE = re.compile(r"<!--\s*req:\s*[-a-zA-Z0-9_.]+;\s*source:\s*([^#]+)#L\d+(?:-L\d+)?\s*-->")
FORBIDDEN_SPEC_PHRASES = (
    "This page is generated from extracted flashlight facts.",
    "The flashlight artifact defines",
    "defines a `",
)


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


def display_path(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def verify_source_comments(src: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(src.glob("*.md")):
        if path.name in {"SUMMARY.md", "introduction.md", "open-questions.md"}:
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        bullets = [line for line in lines if line.startswith("- ")]
        if not bullets:
            errors.append(f"{display_path(path, repo_root)} has no bullets")
            continue
        for line_no, line in enumerate(lines, start=1):
            if not line.startswith("- "):
                continue
            if "MUST" not in line and "SHOULD" not in line and "MAY" not in line and "<!-- source:" not in line:
                continue
            match = SOURCE_RE.search(line) or REQ_RE.search(line)
            if not match:
                errors.append(f"{display_path(path, repo_root)}:L{line_no} missing source or requirement comment")
                continue
            source_path = repo_root / match.group(1)
            if not source_path.exists():
                errors.append(f"{display_path(path, repo_root)}:L{line_no} references missing source {match.group(1)}")
    return errors


def verify_spec_prose(src: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(src.glob("*.md")):
        if path.name in {"evidence.md"}:
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in FORBIDDEN_SPEC_PHRASES:
            if phrase in text:
                errors.append(f"{display_path(path, repo_root)} contains forbidden artifact-shaped phrase: {phrase!r}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--book", type=Path, default=Path("spec"))
    args = parser.parse_args()

    repo_root = Path.cwd()
    src = args.book / "src"
    errors = verify_summary_links(src) + verify_source_comments(src, repo_root) + verify_spec_prose(src, repo_root)
    if errors:
        print("spec verification failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        raise SystemExit(1)
    print("spec verification passed")


if __name__ == "__main__":
    main()
