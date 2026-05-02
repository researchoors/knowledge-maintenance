#!/usr/bin/env python3
"""Render an mdBook spec from extracted DarkBloom facts."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from html import escape
from pathlib import Path
from typing import Any

SPEC_SECTIONS = {
    "overview": {
        "title": "Overview",
        "kinds": {"evidence", "section"},
        "limit": 36,
    },
    "components": {
        "title": "Components",
        "kinds": {"component"},
        "limit": 80,
    },
    "security": {
        "title": "Security and Trust",
        "kinds": {"claim", "section"},
        "limit": 60,
        "keywords": (
            "security",
            "trust",
            "attestation",
            "encryption",
            "secure enclave",
            "privacy",
            "key",
            "certificate",
        ),
    },
    "operations": {
        "title": "Operations",
        "kinds": {"claim", "section"},
        "limit": 60,
        "keywords": (
            "provider",
            "coordinator",
            "analytics",
            "billing",
            "lifecycle",
            "configuration",
            "telemetry",
            "websocket",
        ),
    },
}


def load_facts(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def source_comment(fact: dict[str, Any]) -> str:
    return f"<!-- source: {fact['source_file']}#{fact['source_lines']} fact: {fact['id']} -->"


def render_statement(statement: str) -> str:
    # Flashlight artifacts sometimes contain placeholder tokens such as
    # `<hex>` or `<base64>`. Escape angle brackets so mdBook does not parse
    # them as unclosed HTML tags.
    return escape(statement.rstrip("."), quote=False) + "."


def fact_line(fact: dict[str, Any]) -> str:
    return f"- {source_comment(fact)} {render_statement(fact['statement'])}"


def matches_section(fact: dict[str, Any], section: dict[str, Any]) -> bool:
    if fact["kind"] not in section["kinds"]:
        return False
    keywords = section.get("keywords")
    if not keywords:
        return True
    haystack = f"{fact['title']} {fact['statement']}".lower()
    return any(keyword in haystack for keyword in keywords)


def write_book_toml(book_dir: Path) -> None:
    (book_dir / "book.toml").write_text(
        """[book]
title = "DarkBloom Spec"
authors = ["DarkBloom Spec Pipeline"]
language = "en"
src = "src"

[output.html]
git-repository-url = "https://github.com/Layr-Labs/darkbloom-spec"
""",
        encoding="utf-8",
    )


def write_summary(src: Path) -> None:
    lines = [
        "# Summary",
        "",
        "[Introduction](introduction.md)",
        "- [Overview](overview.md)",
        "- [Components](components.md)",
        "- [Security and Trust](security.md)",
        "- [Operations](operations.md)",
        "- [Evidence Index](evidence.md)",
        "",
    ]
    (src / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")


def write_intro(src: Path, payload: dict[str, Any]) -> None:
    source = payload.get("source", {})
    content = f"""# DarkBloom Spec

This is a generated mdBook-style specification for DarkBloom / d-inference. It is derived from github-flashlight
artifacts and is intended to make artifact truth reviewable as a formal spec.

Every normative bullet in generated pages carries an HTML source comment of the form
`<!-- source: path#lines fact: id -->`. The source comment is the evidence pointer back to flashlight output.

## Source snapshot

- Source repository: `{source.get("source_repo")}`
- Source commit: `{source.get("source_commit")}`
- Flashlight analysis timestamp: `{source.get("analysis_timestamp")}`
- Artifact path: `{source.get("artifacts_path")}`

Canonical changes are merged only after human PR review. Automation may update artifacts and regenerate this derived
spec, but it does not auto-merge.
"""
    (src / "introduction.md").write_text(content, encoding="utf-8")


def render_section(src: Path, name: str, config: dict[str, Any], facts: list[dict[str, Any]]) -> set[str]:
    selected = [fact for fact in facts if matches_section(fact, config)]
    selected = selected[: int(config["limit"])]
    title = config["title"]
    lines = [f"# {title}", "", "This page is generated from extracted flashlight facts.", ""]
    if not selected:
        lines.append("No facts currently match this section.\n")
    else:
        lines.extend(fact_line(fact) for fact in selected)
        lines.append("")
    (src / f"{name}.md").write_text("\n".join(lines), encoding="utf-8")
    return {fact["id"] for fact in selected}


def write_evidence(src: Path, payload: dict[str, Any], used_ids: set[str]) -> None:
    facts = payload["facts"]
    by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for fact in facts:
        by_file[fact["source_file"]].append(fact)

    lines = ["# Evidence Index", "", "All extracted facts grouped by flashlight artifact source.", ""]
    for source_file in sorted(by_file):
        lines.extend([f"## `{source_file}`", ""])
        for fact in by_file[source_file]:
            marker = "rendered" if fact["id"] in used_ids else "indexed"
            title = escape(str(fact["title"]), quote=False)
            lines.append(f"- {source_comment(fact)} `{marker}` **{title}** — {render_statement(fact['statement'])}")
        lines.append("")
    (src / "evidence.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--facts", type=Path, default=Path("facts/darkbloom.facts.json"))
    parser.add_argument("--book", type=Path, default=Path("spec"))
    args = parser.parse_args()

    payload = load_facts(args.facts)
    facts = sorted(
        payload["facts"],
        key=lambda fact: (fact["kind"], fact["source_file"], fact["source_lines"], fact["id"]),
    )
    src = args.book / "src"
    src.mkdir(parents=True, exist_ok=True)

    write_book_toml(args.book)
    write_summary(src)
    write_intro(src, payload)

    used_ids: set[str] = set()
    for name, config in SPEC_SECTIONS.items():
        used_ids |= render_section(src, name, config, facts)
    write_evidence(src, payload, used_ids)
    print(f"rendered {len(facts)} facts into {args.book}")


if __name__ == "__main__":
    main()
