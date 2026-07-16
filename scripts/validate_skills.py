#!/usr/bin/env python3
"""Validate the nanolama skills library.

For every skill under ``skills/<name>/SKILL.md`` this checks:

  * valid YAML frontmatter delimited by ``---`` fences;
  * ``name`` present, equal to the directory name, matching the Agent Skills
    spec (<=64 chars, ``[a-z0-9-]``, no reserved words ``anthropic``/``claude``);
  * ``description`` present, non-empty, <=1024 chars, third person, carrying a
    ``Use when ...`` trigger clause, with no XML tags;
  * only portable frontmatter fields are used;
  * the body is non-trivial and contains the house section headings;
  * every backticked cross-reference under ``## See also`` names a real skill.

It also checks ``scripts/catalog.yaml`` is in 1:1 sync with ``skills/``.

Exit code 0 = green, 1 = one or more problems, 2 = environment error.
Pure standard library plus PyYAML.

    python scripts/validate_skills.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - environment guard
    print("PyYAML is required: pip install -r requirements-dev.txt", file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
CATALOG = ROOT / "scripts" / "catalog.yaml"

NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")
RESERVED_WORDS = ("anthropic", "claude")
XML_TAG_RE = re.compile(r"<[^>]+>")
FIRST_PERSON_RE = re.compile(r"\b(I can|I will|I'll|you can|you should|you'll)\b", re.IGNORECASE)
DESCRIPTION_MAX = 1024
BODY_MIN = 200

# Frontmatter fields that are portable across every Skills surface (API,
# claude.ai, Claude Code). Anything else risks silently not working somewhere.
ALLOWED_FIELDS = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}

# House sections every nanolama skill must carry, for a consistent library.
REQUIRED_SECTIONS = (
    "## When to use",
    "## Pattern",
    "## Adapt to your repo",
    "## Gotchas",
    "## See also",
)

VALID_CATEGORIES_FALLBACK = set()  # populated from catalog at runtime
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def parse_skill(path: Path):
    """Return (meta, body, error). error is None on success."""
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None, None, "missing or malformed YAML frontmatter (--- ... ---)"
    raw, body = match.group(1), match.group(2)
    try:
        meta = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        return None, None, f"invalid YAML frontmatter: {exc}"
    if not isinstance(meta, dict):
        return None, None, "frontmatter is not a mapping"
    return meta, body, None


def check_skill(skill_dir: Path, all_names: set[str]) -> list[str]:
    errors: list[str] = []
    name_dir = skill_dir.name
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [f"{name_dir}: missing SKILL.md"]

    meta, body, err = parse_skill(skill_md)
    if err:
        return [f"{name_dir}/SKILL.md: {err}"]

    name = meta.get("name")
    if not name:
        errors.append(f"{name_dir}: frontmatter missing required `name`")
    else:
        name = str(name)
        if name != name_dir:
            errors.append(f"{name_dir}: frontmatter name '{name}' must equal the directory name")
        if not NAME_RE.match(name):
            errors.append(f"{name_dir}: name must be <=64 chars of [a-z0-9-]")
        for word in RESERVED_WORDS:
            if word in name.lower():
                errors.append(f"{name_dir}: name must not contain reserved word '{word}'")

    desc = meta.get("description")
    if not desc or not str(desc).strip():
        errors.append(f"{name_dir}: frontmatter missing required `description`")
    else:
        desc = str(desc)
        if len(desc) > DESCRIPTION_MAX:
            errors.append(f"{name_dir}: description is {len(desc)} chars (>{DESCRIPTION_MAX})")
        if XML_TAG_RE.search(desc):
            errors.append(f"{name_dir}: description must not contain XML tags")
        if "use when" not in desc.lower():
            errors.append(f"{name_dir}: description must contain a 'Use when ...' trigger clause")
        if FIRST_PERSON_RE.search(desc):
            errors.append(f"{name_dir}: description must be third person (no 'I'/'you' phrasing)")

    for field in meta:
        if field not in ALLOWED_FIELDS:
            errors.append(
                f"{name_dir}: non-portable frontmatter field '{field}' "
                f"(allowed: {', '.join(sorted(ALLOWED_FIELDS))})"
            )

    if body is not None:
        if len(body.strip()) < BODY_MIN:
            errors.append(f"{name_dir}: body is too thin (<{BODY_MIN} chars)")
        for section in REQUIRED_SECTIONS:
            if section not in body:
                errors.append(f"{name_dir}: body missing required section '{section}'")
        errors.extend(_check_cross_refs(name_dir, body, all_names))

    return errors


def _check_cross_refs(name_dir: str, body: str, all_names: set[str]) -> list[str]:
    """Every `backticked` token in the 'See also' section must be a real skill."""
    errors: list[str] = []
    idx = body.find("## See also")
    if idx == -1:
        return errors
    section = body[idx:]
    # The "See also" section is exclusively for skill cross-references, so every
    # backticked lowercase token in it must resolve to a real skill (catches typos).
    for token in re.findall(r"`([a-z0-9-]+)`", section):
        if token not in all_names:
            errors.append(f"{name_dir}: 'See also' references unknown skill `{token}`")
    return errors


def check_catalog(all_names: set[str]) -> list[str]:
    errors: list[str] = []
    if not CATALOG.is_file():
        return [f"missing catalog file: {CATALOG}"]
    data = yaml.safe_load(CATALOG.read_text(encoding="utf-8")) or {}

    category_ids = {c.get("id") for c in data.get("categories", [])}
    listed = [s.get("name") for s in data.get("skills", [])]
    listed_set = set(listed)

    if len(listed) != len(listed_set):
        errors.append("catalog.yaml: duplicate skill entries")
    for skill in data.get("skills", []):
        sname = skill.get("name")
        if skill.get("category") not in category_ids:
            errors.append(f"catalog.yaml: '{sname}' has unknown category '{skill.get('category')}'")
        if not skill.get("blurb"):
            errors.append(f"catalog.yaml: '{sname}' is missing a blurb")

    for missing in sorted(all_names - listed_set):
        errors.append(f"catalog.yaml: skills/{missing}/ exists but is not listed in the catalog")
    for extra in sorted(listed_set - all_names):
        errors.append(f"catalog.yaml: lists '{extra}' but skills/{extra}/SKILL.md is missing")
    return errors


def collect_errors() -> tuple[list[str], int]:
    skill_dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())
    all_names = {p.name for p in skill_dirs}
    errors: list[str] = []
    for skill_dir in skill_dirs:
        errors.extend(check_skill(skill_dir, all_names))
    errors.extend(check_catalog(all_names))
    return errors, len(skill_dirs)


def main() -> int:
    if not SKILLS_DIR.is_dir():
        print(f"no skills/ directory at {SKILLS_DIR}", file=sys.stderr)
        return 1
    errors, count = collect_errors()
    if errors:
        print(f"FAIL - {len(errors)} problem(s) across {count} skill(s):")
        for err in errors:
            print(f"  - {err}")
        return 1
    print(f"OK - {count} skills valid, catalog in sync.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
