#!/usr/bin/env python3
"""Validate the nanolama skills library.

For every skill under ``skills/<name>/SKILL.md`` this checks:

  * valid YAML frontmatter delimited by ``---`` fences;
  * ``name`` present, equal to the directory name, matching the Agent Skills
    spec (<=64 chars, ``[a-z0-9-]``, no reserved words ``anthropic``/``claude``);
  * ``description`` present, 40-1024 chars, third person, carrying a
    ``Use when ...`` trigger clause, no XML tags, and unique across skills;
  * only portable frontmatter fields are used, and ``allowed-tools`` /
    ``disallowed-tools`` (if present) are a string or a list of strings;
  * the body is non-trivial and contains the house section headings IN ORDER;
  * every ``backticked`` cross-reference under ``## See also`` names a real skill;
  * every local markdown link to a bundled file resolves to a file that exists.

It also checks ``scripts/catalog.yaml`` is in 1:1 sync with ``skills/``.

Per-skill ``license`` frontmatter is optional: the repository LICENSE (MIT)
applies to every skill unless a skill overrides it.

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
MARKDOWN_LINK_RE = re.compile(r"\]\(([^)]+)\)")
# Only markdown links that clearly point at a bundled file are link-checked; this
# avoids flagging illustrative, non-file link text.
LOCAL_FILE_HINT_RE = re.compile(r"\.(md|py|png|svg|jpe?g|json|ya?ml|txt|sh|toml|mjs|ts)$", re.IGNORECASE)

DESCRIPTION_MAX = 1024
DESCRIPTION_MIN = 40
BODY_MIN = 200

# Frontmatter fields that are portable across every Skills surface (API,
# claude.ai, Claude Code). Anything else risks silently not working somewhere.
ALLOWED_FIELDS = {
    "name", "description", "license", "allowed-tools",
    "disallowed-tools", "metadata", "compatibility",
}
TOOL_LIST_FIELDS = ("allowed-tools", "disallowed-tools")

# House sections every nanolama skill must carry, in this order.
REQUIRED_SECTIONS = (
    "## When to use",
    "## Pattern",
    "## Adapt to your repo",
    "## Gotchas",
    "## See also",
)

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
        stripped = desc.strip()
        if len(desc) > DESCRIPTION_MAX:
            errors.append(f"{name_dir}: description is {len(desc)} chars (>{DESCRIPTION_MAX})")
        if len(stripped) < DESCRIPTION_MIN:
            errors.append(f"{name_dir}: description is only {len(stripped)} chars (<{DESCRIPTION_MIN}) - too thin to trigger well")
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
    for tool_field in TOOL_LIST_FIELDS:
        if tool_field in meta and not _valid_tool_field(meta[tool_field]):
            errors.append(f"{name_dir}: '{tool_field}' must be a string or a list of strings")

    if body is not None:
        if len(body.strip()) < BODY_MIN:
            errors.append(f"{name_dir}: body is too thin (<{BODY_MIN} chars)")
        for section in REQUIRED_SECTIONS:
            if section not in body:
                errors.append(f"{name_dir}: body missing required section '{section}'")
        errors.extend(_check_section_order(name_dir, body))
        errors.extend(_check_cross_refs(name_dir, body, all_names))
        errors.extend(_check_local_links(name_dir, skill_dir, body))

    return errors


def _valid_tool_field(value) -> bool:
    if isinstance(value, str):
        return True
    if isinstance(value, list):
        return all(isinstance(item, str) for item in value)
    return False


def _check_section_order(name_dir: str, body: str) -> list[str]:
    """The required headings that ARE present must appear in canonical order."""
    present = [(body.find(sec), sec) for sec in REQUIRED_SECTIONS if sec in body]
    found_order = [sec for _, sec in sorted(present)]
    expected_order = [sec for sec in REQUIRED_SECTIONS if sec in {s for _, s in present}]
    if found_order != expected_order:
        return [
            f"{name_dir}: house sections out of order - "
            f"expected {expected_order}, found {found_order}"
        ]
    return []


def _check_cross_refs(name_dir: str, body: str, all_names: set[str]) -> list[str]:
    """Every `backticked` token in the 'See also' section must be a real skill."""
    errors: list[str] = []
    idx = body.find("## See also")
    if idx == -1:
        return errors
    section = body[idx:]
    for token in re.findall(r"`([a-z0-9-]+)`", section):
        if token not in all_names:
            errors.append(f"{name_dir}: 'See also' references unknown skill `{token}`")
    return errors


def _check_local_links(name_dir: str, skill_dir: Path, body: str) -> list[str]:
    """Local markdown links that point at a bundled file must resolve."""
    errors: list[str] = []
    for target in MARKDOWN_LINK_RE.findall(body):
        raw = target.strip()
        if raw.startswith(("http://", "https://", "#", "mailto:")):
            continue
        rel = raw.split("#", 1)[0].strip()
        if not rel:
            continue
        # Only enforce links that clearly reference a bundled file.
        if not (LOCAL_FILE_HINT_RE.search(rel) or rel.startswith(("reference/", "scripts/"))):
            continue
        if not (skill_dir / rel).exists():
            errors.append(f"{name_dir}: broken local link `{raw}` (no file at {rel})")
    return errors


def check_duplicate_descriptions(skill_dirs: list[Path]) -> list[str]:
    """No two skills may share the same description (whitespace-normalized)."""
    errors: list[str] = []
    seen: dict[str, str] = {}
    for skill_dir in skill_dirs:
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            continue
        meta, _body, err = parse_skill(skill_md)
        if err or not isinstance(meta, dict):
            continue
        desc = str(meta.get("description", "")).strip().lower()
        if not desc:
            continue
        norm = re.sub(r"\s+", " ", desc)
        if norm in seen:
            errors.append(
                f"duplicate description: '{skill_dir.name}' and '{seen[norm]}' "
                "share the same description"
            )
        else:
            seen[norm] = skill_dir.name
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
    errors.extend(check_duplicate_descriptions(skill_dirs))
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
