#!/usr/bin/env python3
"""Print the CURRENT version + support window of each nanolama stack technology.

Queries live sources so you never rely on a stale number:
  - https://endoflife.date/api/<product>.json  (support/EOL cycles)
  - https://pypi.org/pypi/<pkg>/json            (latest Python package)
  - https://registry.npmjs.org/<pkg>/latest     (latest npm package)

Run:  python check_versions.py
Needs outbound HTTPS. Standard library only (no pip install).

This gives you the raw NUMBERS. It does NOT decide LTS-vs-latest for you: for
endoflife.date the newest cycle is printed first, which for Django is the newest
release (e.g. 6.x), not necessarily the current LTS (e.g. 5.2). Apply judgment and
cross-check the vendor page (djangoproject.com/download, nodejs.org) — see SKILL.md.
"""
from __future__ import annotations

import json
import sys
import urllib.request

TIMEOUT = 10  # seconds; these are small JSON docs

EOL_PRODUCTS = ["python", "django", "postgresql", "nodejs", "nextjs", "redis"]
PYPI_PKGS = [
    "djangorestframework", "djangorestframework-simplejwt", "dj-rest-auth",
    "celery", "channels", "channels-redis", "daphne", "uvicorn", "gunicorn",
]
NPM_PKGS = [
    "next", "react", "@tanstack/react-query", "zustand", "zod",
    "tailwindcss", "next-intl", "shadcn", "pnpm",
]


def _get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "nanolama-version-check"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:  # noqa: S310 (trusted hosts)
        return json.load(resp)


def eol_summary(product: str) -> str:
    top = _get(f"https://endoflife.date/api/{product}.json")[0]  # newest cycle first
    eol = top.get("eol")
    if eol is False:      # endoflife.date uses false = no EOL scheduled
        eol = "not set"
    elif eol is True:     # true = already end-of-life
        eol = "reached"
    return f"cycle {top.get('cycle')} (latest {top.get('latest', '?')}, eol {eol})"


def pypi_version(pkg: str) -> str:
    return _get(f"https://pypi.org/pypi/{pkg}/json")["info"]["version"]


def npm_version(pkg: str) -> str:
    return _get(f"https://registry.npmjs.org/{pkg}/latest")["version"]


def _row(label: str, width: int, fn) -> bool:
    """Print one row. Returns True on success, False on a fetch/parse error."""
    try:
        print(f"  {label:<{width}} {fn()}")
        return True
    except Exception as exc:  # one dead source must not abort the whole run
        print(f"  {label:<{width}} ERROR ({exc})")
        return False


def main() -> int:
    failures = 0
    print("Live version check - 'latest' is not 'LTS' is not 'supported'. Verify LTS on vendor pages.\n")
    print("== Support / EOL (endoflife.date; newest cycle first) ==")
    for product in EOL_PRODUCTS:
        failures += not _row(product, 14, lambda p=product: eol_summary(p))
    print("\n== Python packages (PyPI latest) ==")
    for pkg in PYPI_PKGS:
        failures += not _row(pkg, 34, lambda p=pkg: pypi_version(p))
    print("\n== npm packages (registry latest) ==")
    for pkg in NPM_PKGS:
        failures += not _row(pkg, 26, lambda p=pkg: npm_version(p))
    print("\nDjango LTS: djangoproject.com/download  |  Node LTS: nodejs.org  |  AWS runtimes lag upstream.")
    if failures:
        print(f"\n{failures} lookup(s) failed - version data is incomplete.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
