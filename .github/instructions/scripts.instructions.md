---
applyTo: "**/scripts/*.py"
---

# Maintainer guide — validation scripts

This repository contains two distinct validation scripts with different scopes.
Understanding their relationship is essential before modifying either.

## scripts/validate_skills.py — repo-authoritative validator

**When it runs:** CI (`make validate`) on every PR that touches `skills/**`.

**What makes it repo-specific:**
- Scans all skills to enforce **name uniqueness** across the repository.
- Enforces the **valid category list** (`VALID_CATEGORIES`).
- Requires **`metadata.author`** to start with `"Canonical"`.
- Requires **`license: Apache-2.0`**.
- Requires **`metadata.summary`** (mandatory in this repo; the website needs it).

## skills/meta/generate-agent-skills/scripts/validate_skill.py — portable baseline

**When it runs:** When contributors author skills in *other* repositories using
the `generate-agent-skills` skill. It is a fallback for repos that have no
`make validate` target.

**What it intentionally omits:**
- Name uniqueness (it sees only one skill at a time).
- Category list enforcement (categories differ per repo).
- `Canonical` author / `Apache-2.0` license requirements (other orgs, other rules).
- `metadata.summary` is advisory-only (other repos may not have a listing site).

## Shared spec checks — keep in sync

When you modify either script, ensure these checks remain consistent between the two:

| Check | Enforcement level |
|---|---|
| `name` regex `^[a-z0-9][a-z0-9-]*[a-z0-9]$` | error |
| `name` matches folder name | error |
| `metadata.version` SemVer `X.Y.Z` | error |
| `description` has a `WHEN:` clause | warning |
| `description` ≤ 1,024 characters | error |
| `metadata.summary` ≤ 160 characters | error (`validate_skills.py`) / warning (`validate_skill.py`) |
| `metadata.tags` present | warning |

**If you change a threshold or add a new shared check, update both files.**
