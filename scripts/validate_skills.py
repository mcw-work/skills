#!/usr/bin/env python3
"""
Validate all SKILL.md files in the canonical/skills repository.

Checks every skill against the canonical/skills frontmatter standard, which
follows the agentskills.io specification (https://agentskills.io/specification):

  Top-level fields (spec-standard):
    - Required: name, description, license
  Under metadata: (spec-standard location for arbitrary key-value pairs):
    - Required: metadata.author, metadata.version
    - Recommended: metadata.tags

  Rules:
    - name: lowercase kebab-case, unique across the repo; may start with a digit (e.g. 12factor-app)
    - metadata.version: semantic versioning (X.Y.Z)
    - metadata.author: starts with "Canonical" (e.g. "Canonical" or "Canonical/<team>")
    - metadata.summary: recommended short human-readable blurb (≤ 160 chars) for display
    - license: "Apache-2.0"
    - description: minimum length, presence of trigger phrases
    - directory: each skill folder contains exactly one SKILL.md

Usage:
    python scripts/validate_skills.py [--warn-only] [--path PATH]

Options:
    --warn-only   Exit 0 even when errors are found (useful for reporting).
    --path PATH   Root of the repository (default: parent of this script's dir).

Exit codes:
    0 — All validations passed (or --warn-only was set).
    1 — One or more validation errors found.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Top-level fields required by this repo (subset of the agentskills.io spec)
REQUIRED_FIELDS: set[str] = {"name", "description", "license"}
# Fields required under the spec-standard `metadata:` mapping
REQUIRED_METADATA_FIELDS: set[str] = {"author", "version"}
# Recommended (warning only) metadata sub-fields
RECOMMENDED_METADATA_FIELDS: set[str] = {"tags", "summary"}

SUMMARY_MAX_CHARS = 160

EXPECTED_AUTHOR_PREFIX = "Canonical"
EXPECTED_LICENSE = "Apache-2.0"

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
_KEBAB_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")
_TRIGGER_RES = [
    re.compile(r"\bWHEN\s*:", re.IGNORECASE),
    re.compile(r"\bactivat", re.IGNORECASE),
    re.compile(r"\btrigger\b", re.IGNORECASE),
]

MIN_DESCRIPTION_WORDS = 20

VALID_CATEGORIES = {"meta", "products", "engineering", "documentation", "operations", "security", "practices"}

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Issue:
    level: str  # "error" | "warning"
    message: str


@dataclass
class SkillResult:
    path: Path
    issues: list[Issue] = field(default_factory=list)
    name: Optional[str] = None

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body) from a markdown file."""
    if not content.startswith("---"):
        return {}, content
    end = content.find("\n---", 3)
    if end == -1:
        return {}, content
    try:
        fm = yaml.safe_load(content[3:end])
        return (fm or {}), content[end + 4:]
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML frontmatter: {exc}") from exc


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_skill(skill_md: Path, skills_root: Path) -> SkillResult:
    result = SkillResult(path=skill_md)

    # Directory should contain exactly one SKILL.md
    siblings = list(skill_md.parent.glob("SKILL.md"))
    if len(siblings) != 1:
        result.issues.append(Issue(
            "error",
            f"Expected exactly one SKILL.md in {skill_md.parent.name}/, found {len(siblings)}",
        ))

    # Category check (first path component under skills/)
    try:
        rel = skill_md.relative_to(skills_root)
        category = rel.parts[0]
        if category not in VALID_CATEGORIES:
            result.issues.append(Issue(
                "warning",
                f"Skill is in category '{category}', which is not a recognised top-level namespace "
                f"({', '.join(sorted(VALID_CATEGORIES))}). Add it to VALID_CATEGORIES in the "
                "validation script if intentional.",
            ))
    except ValueError:
        pass

    # Read content
    try:
        content = skill_md.read_text(encoding="utf-8")
    except OSError as exc:
        result.issues.append(Issue("error", f"Cannot read file: {exc}"))
        return result

    # Parse frontmatter
    try:
        frontmatter, _body = parse_frontmatter(content)
    except ValueError as exc:
        result.issues.append(Issue("error", str(exc)))
        return result

    if not frontmatter:
        result.issues.append(Issue(
            "error",
            "No YAML frontmatter found. File must begin with a --- block containing at least "
            "name, description, and license; and a metadata: block with author and version.",
        ))
        return result

    # Required top-level fields
    for fname in sorted(REQUIRED_FIELDS):
        val = frontmatter.get(fname)
        if val is None or str(val).strip() == "":
            result.issues.append(Issue("error", f"Missing or empty required field: '{fname}'"))

    # metadata: block — must be a mapping
    metadata = frontmatter.get("metadata")
    if metadata is None:
        for fname in sorted(REQUIRED_METADATA_FIELDS):
            result.issues.append(Issue("error", f"Missing or empty required field: 'metadata.{fname}'"))
        for fname in sorted(RECOMMENDED_METADATA_FIELDS):
            result.issues.append(Issue("warning", f"Missing recommended field: 'metadata.{fname}'"))
        metadata = {}
    elif not isinstance(metadata, dict):
        result.issues.append(Issue("error", "'metadata' must be a key-value mapping."))
        metadata = {}
    else:
        for fname in sorted(REQUIRED_METADATA_FIELDS):
            val = metadata.get(fname)
            if val is None or str(val).strip() == "":
                result.issues.append(Issue("error", f"Missing or empty required field: 'metadata.{fname}'"))
        for fname in sorted(RECOMMENDED_METADATA_FIELDS):
            val = metadata.get(fname)
            if val is None or (isinstance(val, list) and len(val) == 0):
                result.issues.append(Issue("warning", f"Missing recommended field: 'metadata.{fname}'"))

    # name — kebab-case, matches folder name
    name = frontmatter.get("name")
    if name:
        result.name = str(name).strip()
        if not _KEBAB_RE.match(result.name):
            result.issues.append(Issue(
                "error",
                f"'name' must be lowercase kebab-case (letters, digits, hyphens). Got: '{result.name}'",
            ))
        folder_name = skill_md.parent.name
        if result.name != folder_name:
            result.issues.append(Issue(
                "warning",
                f"'name' value ('{result.name}') does not match the folder name ('{folder_name}'). "
                "They should be identical for consistent discovery.",
            ))

    # metadata.version — semver
    version = str(metadata.get("version", "")).strip()
    if version and not _SEMVER_RE.match(version):
        result.issues.append(Issue(
            "error",
            f"'metadata.version' must follow SemVer format X.Y.Z. Got: '{version}'",
        ))

    # metadata.author
    author = str(metadata.get("author", "")).strip()
    if author and not author.startswith(EXPECTED_AUTHOR_PREFIX):
        result.issues.append(Issue(
            "warning",
            f"'metadata.author' should start with '{EXPECTED_AUTHOR_PREFIX}' (e.g. 'Canonical' or 'Canonical/<team>'). Got: '{author}'",
        ))

    # metadata.summary — optional but recommended; must be concise
    summary = str(metadata.get("summary", "")).strip()
    if summary and len(summary) > SUMMARY_MAX_CHARS:
        result.issues.append(Issue(
            "warning",
            f"'metadata.summary' is {len(summary)} chars (recommended max: {SUMMARY_MAX_CHARS}). "
            "Keep it short — it is displayed on skill cards.",
        ))

    # license — top-level, per agentskills.io spec
    license_val = str(frontmatter.get("license", "")).strip()
    if license_val and license_val != EXPECTED_LICENSE:
        result.issues.append(Issue(
            "error",
            f"'license' must be '{EXPECTED_LICENSE}'. Got: '{license_val}'",
        ))

    # description quality
    description = str(frontmatter.get("description", "")).strip()
    if description:
        word_count = len(description.split())
        if word_count < MIN_DESCRIPTION_WORDS:
            result.issues.append(Issue(
                "warning",
                f"'description' has only {word_count} words (minimum recommended: {MIN_DESCRIPTION_WORDS}). "
                "A longer description with explicit trigger keywords improves agent activation accuracy.",
            ))
        if not any(pat.search(description) for pat in _TRIGGER_RES):
            result.issues.append(Issue(
                "warning",
                "'description' contains no apparent trigger phrases. Add a 'WHEN: ...' clause listing "
                "the keywords or scenarios that should activate this skill.",
            ))

    return result


def check_name_uniqueness(results: list[SkillResult]) -> None:
    seen: dict[str, Path] = {}
    for result in results:
        if not result.name:
            continue
        if result.name in seen:
            result.issues.append(Issue(
                "error",
                f"Duplicate skill name '{result.name}' — also used in {seen[result.name]}. "
                "Every skill must have a unique 'name' value.",
            ))
        else:
            seen[result.name] = result.path


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

_RESET = "\033[0m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_GREEN = "\033[32m"
_BOLD = "\033[1m"


def _c(text: str, *codes: str) -> str:
    """Wrap text in ANSI codes if stdout is a TTY."""
    if sys.stdout.isatty():
        return "".join(codes) + text + _RESET
    return text


def report(results: list[SkillResult], skills_root: Path) -> tuple[int, int]:
    total_errors = total_warnings = 0

    for r in results:
        rel = r.path.relative_to(skills_root.parent)
        if not r.issues:
            print(f"  {_c('✓', _GREEN)}  {rel}")
            continue

        icon = _c("✗", _RED) if r.errors else _c("⚠", _YELLOW)
        print(f"  {icon}  {_c(str(rel), _BOLD)}")
        for issue in r.issues:
            if issue.level == "error":
                print(f"        {_c('ERROR:', _RED, _BOLD)} {issue.message}")
            else:
                print(f"        {_c('WARN: ', _YELLOW, _BOLD)} {issue.message}")
        total_errors += len(r.errors)
        total_warnings += len(r.warnings)

    return total_errors, total_warnings


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate SKILL.md files in the canonical/skills repository.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Exit 0 even when validation errors are found.",
    )
    parser.add_argument(
        "--path",
        default=None,
        help="Repository root (default: parent directory of this script).",
    )
    args = parser.parse_args()

    repo_root = Path(args.path) if args.path else Path(__file__).parent.parent
    skills_root = repo_root / "skills"

    if not skills_root.exists():
        print(f"ERROR: skills/ directory not found at {skills_root}", file=sys.stderr)
        return 1

    skill_files = sorted(skills_root.rglob("SKILL.md"))

    if not skill_files:
        print("No SKILL.md files found — nothing to validate.")
        return 0

    print(f"\nValidating {len(skill_files)} skill(s) in {skills_root.relative_to(repo_root)}/\n")

    results = [validate_skill(f, skills_root) for f in skill_files]
    check_name_uniqueness(results)

    total_errors, total_warnings = report(results, skills_root)

    print(f"\n{'─' * 60}")
    print(f"  Skills checked : {len(skill_files)}")
    print(f"  Errors         : {_c(str(total_errors), _RED, _BOLD) if total_errors else str(total_errors)}")
    print(f"  Warnings       : {_c(str(total_warnings), _YELLOW) if total_warnings else str(total_warnings)}")
    print(f"{'─' * 60}\n")

    if total_errors > 0:
        if args.warn_only:
            print("Validation finished with errors (--warn-only: treating as warnings).\n")
            return 0
        print("Validation FAILED. Fix the errors above before opening a PR.\n")
        return 1

    if total_warnings > 0:
        print("Validation passed with warnings — consider addressing them.\n")
    else:
        print(_c("All validations passed ✓\n", _GREEN, _BOLD))

    return 0


if __name__ == "__main__":
    sys.exit(main())
