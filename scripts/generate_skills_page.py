#!/usr/bin/env python3
"""
Generate a GitHub Pages site (docs/index.html) listing all skills in
the canonical/skills repository.

Reads scripts/template.html, populates it with skill data, and writes
docs/index.html.

Usage:
    python scripts/generate_skills_page.py [--path PATH] [--out OUT]

Options:
    --path PATH   Repository root (default: parent of this script's dir).
    --out OUT     Output HTML file (default: <repo_root>/docs/index.html).
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Run: uv sync", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

CATEGORY_LABELS: dict[str, str] = {
    "meta":          "Meta — Skill Authoring Tools",
    "products":      "Products",
    "engineering":   "Engineering",
    "documentation": "Documentation",
    "practices":     "Practices",
    "operations":    "Operations",
    "security":      "Security",
}

CATEGORY_DESCRIPTIONS: dict[str, str] = {
    "meta":          "Skills for creating, validating, and refining other skills.",
    "products":      "Skills scoped to specific Canonical products and technologies.",
    "engineering":   "Cross-product engineering expertise and workflow patterns.",
    "documentation": "Documentation standards, Diataxis practices, and review workflows.",
    "practices":     "Cross-functional ways of working: planning, delivery, and retrospectives.",
    "operations":    "Infrastructure, deployment, and operational runbooks.",
    "security":      "Security practices, compliance, and threat modelling.",
}

CATEGORY_ORDER = [
    "meta", "products", "engineering", "documentation",
    "practices", "operations", "security",
]


@dataclass
class Skill:
    path: Path
    category: str
    subcategory: str   # non-empty only for products/<product>/<skill>/
    skill_rel: str     # e.g. "engineering/my-skill" — used for GitHub URL
    name: str
    description: str
    summary: str
    version: str
    tags: list[str] = field(default_factory=list)

    @property
    def display_description(self) -> str:
        """Summary if provided, otherwise description with WHEN: clause stripped."""
        if self.summary:
            return self.summary
        return re.sub(r"\s*WHEN\s*:.*", "", self.description, flags=re.IGNORECASE | re.DOTALL).strip()

    @property
    def short_description(self) -> str:
        """Description with the WHEN: clause stripped for display."""
        return re.sub(r"\s*WHEN\s*:.*", "", self.description, flags=re.IGNORECASE | re.DOTALL).strip()

    @property
    def trigger_phrases(self) -> list[str]:
        m = re.search(r"WHEN\s*:(.*)", self.description, re.IGNORECASE | re.DOTALL)
        if not m:
            return []
        return [t.strip().rstrip(".") for t in re.split(r"[,;]", m.group(1)) if t.strip()]

    @property
    def github_url(self) -> str:
        return f"https://github.com/canonical/skills/tree/main/skills/{self.skill_rel}"

    @property
    def install_cmd(self) -> str:
        return f"npx skills add canonical/skills --skill {self.name}"


def load_skill(skill_md: Path, skills_root: Path) -> Optional[Skill]:
    try:
        content = skill_md.read_text(encoding="utf-8")
    except OSError:
        return None

    if not content.startswith("---"):
        return None
    end = content.find("\n---", 3)
    if end == -1:
        return None
    try:
        fm = yaml.safe_load(content[3:end]) or {}
    except yaml.YAMLError:
        return None

    if not fm.get("name"):
        return None

    rel_parts = skill_md.relative_to(skills_root).parts
    category    = rel_parts[0] if rel_parts else "other"
    subcategory = rel_parts[1] if category == "products" and len(rel_parts) > 2 else ""
    skill_rel   = "/".join(rel_parts[:-1])

    metadata_fm = fm.get("metadata") or {}
    tags_raw = metadata_fm.get("tags", [])
    tags = list(tags_raw) if isinstance(tags_raw, list) else ([str(tags_raw)] if tags_raw else [])

    return Skill(
        path=skill_md,
        category=category,
        subcategory=subcategory,
        skill_rel=skill_rel,
        name=str(fm.get("name", "")).strip(),
        description=str(fm.get("description", "")).strip(),
        summary=str(metadata_fm.get("summary", "")).strip(),
        version=str(metadata_fm.get("version", "")).strip(),
        tags=tags,
    )


# ---------------------------------------------------------------------------
# HTML fragment builders
# ---------------------------------------------------------------------------

def _e(text: str) -> str:
    """HTML-escape a value."""
    return html.escape(str(text))


def skill_card(skill: Skill) -> str:
    product_badge = (
        f'<span class="product-badge">{_e(skill.subcategory)}</span> '
        if skill.subcategory else ""
    )
    triggers_html = ""

    tags_html = "".join(f'<span class="tag">{_e(t)}</span>' for t in skill.tags)

    return f"""\
  <article class="card"
           data-name="{_e(skill.name)}"
           data-desc="{_e(skill.display_description)}"
           data-tags="{_e(' '.join(skill.tags))}">
    <div class="card__head">
      <span class="card__name">{product_badge}{_e(skill.name)}</span>
      <span class="card__version">v{_e(skill.version)}</span>
    </div>
    <p class="card__desc">{_e(skill.display_description)}</p>
    {triggers_html}
    <div class="card__foot">
      <div class="tags">{tags_html}</div>
      <div class="card__actions">
        <button class="copy-btn" type="button" data-cmd="{_e(skill.install_cmd)}" aria-label="Copy install command for {_e(skill.name)}">
          <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
          Copy install
        </button>
        <a class="source-link" href="{_e(skill.github_url)}" target="_blank" rel="noopener">
          View source ↗
        </a>
      </div>
    </div>
  </article>"""


def category_section(category: str, skills: list[Skill], subcategories: dict[str, list[Skill]]) -> str:
    label       = _e(CATEGORY_LABELS.get(category, category.title()))
    description = CATEGORY_DESCRIPTIONS.get(category, "")
    count       = len(skills)

    desc_html = f'<p class="section__desc">{_e(description)}</p>' if description else ""

    if category == "products" and subcategories:
        groups = []
        for subcat, sub_skills in sorted(subcategories.items()):
            cards = "\n".join(skill_card(s) for s in sorted(sub_skills, key=lambda s: s.name))
            groups.append(f"""\
  <div class="subcat">
    <p class="subcat__label">{_e(subcat.title())}</p>
    <div class="grid">
{cards}
    </div>
  </div>""")
        inner = "\n".join(groups)
    else:
        cards = "\n".join(skill_card(s) for s in sorted(skills, key=lambda s: s.name))
        inner = f'  <div class="grid">\n{cards}\n  </div>'

    return f"""\
<section class="section" id="cat-{_e(category)}">
  <div class="section__header">
    <h2 class="section__title">{label}</h2>
    <span class="section__count">{count}</span>
  </div>
  {desc_html}
{inner}
</section>"""


def build_nav(ordered: list[str], by_category: dict[str, list]) -> str:
    items = []
    for cat in ordered:
        label = _e(CATEGORY_LABELS.get(cat, cat.title()))
        count = len(by_category[cat])
        items.append(
            f'<a href="#cat-{_e(cat)}" class="cat-nav__tab">'
            f'{label} <span class="cat-count">{count}</span>'
            f'</a>'
        )
    return "\n      ".join(items)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate docs/index.html from canonical/skills SKILL.md files.",
    )
    parser.add_argument("--path", default=None, help="Repository root.")
    parser.add_argument("--out",  default=None, help="Output HTML file path.")
    args = parser.parse_args()

    repo_root   = Path(args.path) if args.path else Path(__file__).parent.parent
    skills_root = repo_root / "skills"
    template    = Path(__file__).parent / "template.html"
    out_file    = Path(args.out) if args.out else repo_root / "docs" / "index.html"

    if not skills_root.exists():
        print(f"ERROR: skills/ directory not found at {skills_root}", file=sys.stderr)
        return 1
    if not template.exists():
        print(f"ERROR: template not found at {template}", file=sys.stderr)
        return 1

    # Load all skills
    skills: list[Skill] = []
    skipped = 0
    for f in sorted(skills_root.rglob("SKILL.md")):
        skill = load_skill(f, skills_root)
        if skill:
            skills.append(skill)
        else:
            print(f"  SKIP: {f} — missing or invalid frontmatter", file=sys.stderr)
            skipped += 1

    # Group by category
    by_category: dict[str, list[Skill]]               = defaultdict(list)
    by_subcategory: dict[str, dict[str, list[Skill]]] = defaultdict(lambda: defaultdict(list))
    for skill in skills:
        by_category[skill.category].append(skill)
        if skill.subcategory:
            by_subcategory[skill.category][skill.subcategory].append(skill)

    ordered = [c for c in CATEGORY_ORDER if c in by_category]
    ordered += sorted(c for c in by_category if c not in ordered)  # any unknown categories last

    # Build HTML fragments
    nav_html      = build_nav(ordered, by_category)
    sections_html = "\n".join(
        category_section(c, by_category[c], dict(by_subcategory.get(c, {})))
        for c in ordered
    )

    skill_word = "skill" if len(skills) == 1 else "skills"
    total_str  = f"{len(skills)} {skill_word}"

    # Render template
    page = template.read_text(encoding="utf-8")
    page = page.replace("%%TOTAL%%",     total_str)
    page = page.replace("%%DATE%%",      date.today().isoformat())
    page = page.replace("%%NAV_ITEMS%%", nav_html)
    page = page.replace("%%SECTIONS%%",  sections_html)

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(page, encoding="utf-8")

    print(f"Generated {out_file} — {len(skills)} skill(s), {skipped} skipped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

