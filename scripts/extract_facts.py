#!/usr/bin/env python3
"""Extract deterministic spec facts from github-flashlight artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Fact:
    id: str
    kind: str
    title: str
    statement: str
    source_file: str
    source_lines: str
    confidence: str = "artifact-derived"


HEADING_RE = re.compile(r"^(#{1,4})\s+(.+?)\s*$")
KEY_LINE_RE = re.compile(r"^\s*(?:[-*]\s+|\d+\.\s+|\|\s*\*\*|\*\*[^*]+\*\*:)")


def stable_id(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]


def rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def line_for_text(lines: list[str], needle: str) -> int:
    for idx, line in enumerate(lines, start=1):
        if needle in line:
            return idx
    return 1


def extract_manifest(artifacts: Path, repo_root: Path) -> list[Fact]:
    path = artifacts / "manifest.json"
    if not path.exists():
        return []
    data = read_json(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    source_repo = data.get("source_repo", "unknown")
    source_commit = data.get("source_commit", "unknown")
    statement = (
        f"Flashlight analyzed {source_repo} at commit {source_commit} "
        f"with {data.get('components', 'unknown')} components and {data.get('citations', 'unknown')} citations."
    )
    line = line_for_text(lines, '"source_repo"')
    return [
        Fact(
            id=stable_id("manifest", statement),
            kind="evidence",
            title="Analyzed source revision",
            statement=statement,
            source_file=rel(path, repo_root),
            source_lines=f"L{line}-L{min(len(lines), line + 6)}",
        )
    ]


def extract_components(artifacts: Path, repo_root: Path) -> list[Fact]:
    path = artifacts / "service_discovery" / "components.json"
    if not path.exists():
        return []
    data = read_json(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    facts: list[Fact] = []
    for component in data.get("components", []):
        name = component.get("name", "unnamed")
        kind = component.get("kind", "component")
        ctype = component.get("type", "unknown")
        root_path = component.get("root_path", "unknown")
        description = component.get("description", "No description provided")
        external = component.get("external_applications") or []
        deps = component.get("internal_dependencies") or []
        extras: list[str] = []
        if deps:
            extras.append(f"internal dependencies: {', '.join(map(str, deps))}")
        if external:
            extras.append(f"external applications: {', '.join(map(str, external))}")
        suffix = f" ({'; '.join(extras)})" if extras else ""
        statement = f"{name} is a {kind} ({ctype}) rooted at `{root_path}`. {description}.{suffix}"
        line = line_for_text(lines, f'"name": "{name}"')
        facts.append(
            Fact(
                id=stable_id("component", name, kind, root_path),
                kind="component",
                title=name,
                statement=statement,
                source_file=rel(path, repo_root),
                source_lines=f"L{line}-L{min(len(lines), line + 12)}",
            )
        )
    return facts


def clean_markdown(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).strip(" |")


def extract_markdown(artifacts: Path, repo_root: Path) -> list[Fact]:
    facts: list[Fact] = []
    for path in sorted(artifacts.rglob("*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        current_heading = path.stem.replace("-", " ").title()
        in_code = False
        for idx, line in enumerate(lines, start=1):
            if line.strip().startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                continue
            heading = HEADING_RE.match(line)
            if heading:
                current_heading = clean_markdown(heading.group(2))
                if len(heading.group(1)) <= 3 and current_heading:
                    facts.append(
                        Fact(
                            id=stable_id("heading", rel(path, repo_root), str(idx), current_heading),
                            kind="section",
                            title=current_heading,
                            statement=f"The flashlight artifact defines a `{current_heading}` section for {path.stem}.",
                            source_file=rel(path, repo_root),
                            source_lines=f"L{idx}",
                        )
                    )
                continue
            if KEY_LINE_RE.match(line) and not re.match(r"^\s*\|[-: ]+\|", line):
                statement = clean_markdown(line)
                if len(statement) < 24 or statement.lower().startswith("component | type"):
                    continue
                facts.append(
                    Fact(
                        id=stable_id("line", rel(path, repo_root), str(idx), statement),
                        kind="claim",
                        title=current_heading,
                        statement=statement,
                        source_file=rel(path, repo_root),
                        source_lines=f"L{idx}",
                    )
                )
    return facts


def extract_facts(artifacts: Path, repo_root: Path) -> dict[str, Any]:
    raw_facts = [
        *extract_manifest(artifacts, repo_root),
        *extract_components(artifacts, repo_root),
        *extract_markdown(artifacts, repo_root),
    ]
    facts = sorted(
        {fact.id: fact for fact in raw_facts}.values(),
        key=lambda fact: (fact.kind, fact.source_file, fact.source_lines, fact.id),
    )
    manifest = read_json(artifacts / "manifest.json") if (artifacts / "manifest.json").exists() else {}
    return {
        "schema_version": 1,
        "source": {
            "artifacts_path": rel(artifacts, repo_root),
            "source_repo": manifest.get("source_repo"),
            "source_commit": manifest.get("source_commit"),
            "analysis_timestamp": manifest.get("analysis_timestamp"),
        },
        "facts": [asdict(fact) for fact in facts],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts/d-inference"))
    parser.add_argument("--out", type=Path, default=Path("facts/darkbloom.facts.json"))
    args = parser.parse_args()

    repo_root = Path.cwd()
    payload = extract_facts(args.artifacts, repo_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(payload['facts'])} facts to {args.out}")


if __name__ == "__main__":
    main()
