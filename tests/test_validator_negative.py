"""Negative + positive fixtures for the nanolama validator.

Builds intentionally-malformed skills in a temp dir and asserts the validator
rejects each with the right error, plus a well-formed case (including modern
optional frontmatter) that must be accepted. Run with:  python -m pytest -q
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import validate_skills  # noqa: E402

# Real skill names, so a fixture's `See also: `verify`` resolves while a bogus
# cross-reference does not.
REAL_NAMES = {p.name for p in validate_skills.SKILLS_DIR.iterdir() if p.is_dir()}

DESC_OK = (
    "Exercises the nanolama validator with a well-formed example fixture. "
    "Use when running the negative-test suite. Not for real use."
)

BODY_OK = """# Example Skill

## When to use
When exercising the validator test fixtures in a controlled, deterministic way.

## Pattern
The invariant under test is that the validator accepts a well-formed skill and
rejects malformed ones. This paragraph pushes the body comfortably past the
minimum length the validator enforces so only the intended rule fails.

## Steps / idioms
1. Build a fixture. 2. Run check_skill. 3. Assert on the returned errors.

## Adapt to your repo
Rename the example fields to your own.

## Gotchas
- This is only a fixture, not a real skill.

## See also
- `verify`
"""


def _skill_text(name="example-skill", description=DESC_OK, extra_fm="", body=BODY_OK):
    frontmatter = f"name: {name}\ndescription: {description}\n"
    if extra_fm:
        frontmatter += extra_fm.rstrip("\n") + "\n"
    return f"---\n{frontmatter}---\n\n{body}"


def _write(tmp_path, dir_name, text):
    d = tmp_path / dir_name
    d.mkdir()
    (d / "SKILL.md").write_text(text, encoding="utf-8")
    return d


def _errors(tmp_path, dir_name, text):
    return validate_skills.check_skill(_write(tmp_path, dir_name, text), REAL_NAMES)


# --- positive: a well-formed skill (and modern optional frontmatter) is accepted ---

def test_wellformed_skill_passes(tmp_path):
    assert _errors(tmp_path, "example-skill", _skill_text()) == []


def test_modern_optional_frontmatter_accepted(tmp_path):
    text = _skill_text(name="tooled-skill", extra_fm="allowed-tools: Bash(git status:*)")
    assert _errors(tmp_path, "tooled-skill", text) == []


def test_license_and_metadata_frontmatter_accepted(tmp_path):
    extra = "license: MIT\nmetadata:\n  author: nanolama"
    text = _skill_text(name="licensed-skill", extra_fm=extra)
    assert _errors(tmp_path, "licensed-skill", text) == []


# --- negative fixtures: (dir_name, text, expected error substring) ---

_LONG_DESC = "Use when testing. " + ("padding " * 220)  # > 1024 chars, no colon, no XML

NEGATIVE_CASES = [
    ("missing-desc", _skill_text(description="").replace("description: \n", ""), "missing required `description`"),
    ("oversized-desc", _skill_text(description=_LONG_DESC), "(>1024)"),
    ("xml-desc", _skill_text(description="Use when testing a <tag> appears here."), "XML tags"),
    ("first-person", _skill_text(description="You should use this. Use when testing."), "third person"),
    ("no-trigger", _skill_text(description="Runs an example for tests only. Not for real."), "Use when"),
    ("thin-desc", _skill_text(description="Use when x."), "too thin"),
    ("name-mismatch", _skill_text(name="not-the-dir"), "must equal the directory name"),
    ("my-claude-tool", _skill_text(name="my-claude-tool"), "reserved word 'claude'"),
    ("nonportable", _skill_text(extra_fm="foo: bar"), "non-portable frontmatter field"),
    ("bad-tools", _skill_text(extra_fm="allowed-tools:\n  a: b"), "must be a string or a list"),
]


@pytest.mark.parametrize("dir_name,text,expected", NEGATIVE_CASES,
                         ids=[c[0] for c in NEGATIVE_CASES])
def test_frontmatter_negatives(tmp_path, dir_name, text, expected):
    errors = _errors(tmp_path, dir_name, text)
    assert any(expected in e for e in errors), f"expected '{expected}' in {errors}"


def test_missing_required_section(tmp_path):
    body = BODY_OK.replace("## Gotchas\n- This is only a fixture, not a real skill.\n\n", "")
    errors = _errors(tmp_path, "no-gotchas", _skill_text(body=body))
    assert any("missing required section '## Gotchas'" in e for e in errors)


def test_sections_out_of_order(tmp_path):
    body = """# X

## When to use
Line one of the fixture.

## Gotchas
- An early gotcha placed before Pattern on purpose.

## Pattern
The pattern text goes here with enough words to clear the body minimum length so
that only the ordering rule is what fails in this particular fixture.

## Adapt to your repo
Rename.

## See also
- `verify`
"""
    errors = _errors(tmp_path, "out-of-order", _skill_text(body=body))
    assert any("out of order" in e for e in errors)


def test_bad_cross_reference(tmp_path):
    body = BODY_OK.replace("- `verify`", "- `nope-skill`")
    errors = _errors(tmp_path, "bad-xref", _skill_text(body=body))
    assert any("unknown skill `nope-skill`" in e for e in errors)


def test_broken_local_link(tmp_path):
    body = BODY_OK.replace(
        "## Adapt to your repo\nRename the example fields to your own.",
        "## Adapt to your repo\nSee [the ref](reference/missing.md).",
    )
    errors = _errors(tmp_path, "broken-link", _skill_text(body=body))
    assert any("broken local link" in e for e in errors)


def test_resolving_local_link_passes(tmp_path):
    d = _write(tmp_path, "with-ref", _skill_text(name="with-ref", body=BODY_OK.replace(
        "## Adapt to your repo\nRename the example fields to your own.",
        "## Adapt to your repo\nSee [the ref](reference/notes.md).",
    )))
    (d / "reference").mkdir()
    (d / "reference" / "notes.md").write_text("# notes\n", encoding="utf-8")
    assert validate_skills.check_skill(d, REAL_NAMES) == []


def test_malformed_frontmatter_rejected(tmp_path):
    text = "no frontmatter here\n\n## When to use\nx\n"
    errors = _errors(tmp_path, "no-fm", text)
    assert any("frontmatter" in e for e in errors)


# --- duplicate-description detection ---

def test_duplicate_descriptions_flagged(tmp_path):
    _write(tmp_path, "dup-a", _skill_text(name="dup-a"))
    _write(tmp_path, "dup-b", _skill_text(name="dup-b"))
    dirs = [tmp_path / "dup-a", tmp_path / "dup-b"]
    errors = validate_skills.check_duplicate_descriptions(dirs)
    assert any("duplicate description" in e for e in errors)


def test_real_skills_have_unique_descriptions():
    dirs = sorted(p for p in validate_skills.SKILLS_DIR.iterdir() if p.is_dir())
    assert validate_skills.check_duplicate_descriptions(dirs) == []
