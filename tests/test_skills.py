"""Green-from-commit-#1 test suite for the nanolama skills library.

These tests enforce the SKILL.md contract and keep the human README in sync
with the machine catalog. Run with:  python -m pytest -q
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import generate_readme  # noqa: E402
import validate_skills  # noqa: E402


def _skill_dirs():
    return sorted(p for p in validate_skills.SKILLS_DIR.iterdir() if p.is_dir())


def test_at_least_one_skill():
    assert _skill_dirs(), "expected at least one skill under skills/"


def test_every_skill_is_valid():
    dirs = _skill_dirs()
    all_names = {p.name for p in dirs}
    errors: list[str] = []
    for skill_dir in dirs:
        errors += validate_skills.check_skill(skill_dir, all_names)
    assert errors == [], "SKILL.md validation failed:\n" + "\n".join(errors)


def test_catalog_matches_disk():
    all_names = {p.name for p in _skill_dirs()}
    errors = validate_skills.check_catalog(all_names)
    assert errors == [], "catalog.yaml is out of sync:\n" + "\n".join(errors)


def test_readme_table_in_sync():
    table = generate_readme.render_table()
    current = generate_readme.README.read_text(encoding="utf-8")
    assert current == generate_readme.splice(current, table), (
        "README.md is out of sync with catalog.yaml - "
        "run: python scripts/generate_readme.py"
    )
