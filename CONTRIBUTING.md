# Contributing to canonical/skills

Thank you for contributing! This guide walks you through everything you need to
add or improve a skill in this repository.

---

## Prerequisites

- **Node.js 18+** (`npx` is used to install skills)
- **Python 3.10+** and **[uv](https://docs.astral.sh/uv/)** (for local validation)
- **Git** and a GitHub account
- **`generate-agent-skills` skill** — strongly recommended before authoring any
  skill (see Step 1)

Install uv if you don't have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install all project dependencies once:

```bash
make install
```

All local commands in this guide use `make`. Run `make help` to see available
targets.

---

## Step 1 — Install and Use `generate-agent-skills`

Before writing a `SKILL.md` from scratch, install the `generate-agent-skills`
skill from this repository. It is specifically designed for skill authoring and
will guide your agent through purpose scoping, trigger-phrase writing,
frontmatter authoring, body structuring, and the pre-submission checklist.

Install it locally (for the current project) or globally:

```bash
# local — scoped to your current working directory
npx skills add canonical/skills --skill generate-agent-skills

# global — available in any project
npx skills add canonical/skills --skill generate-agent-skills --global
```

Once installed, ask your agent:

> "Help me create a new agent skill for [describe what your skill should do].
> Walk me through the purpose, description, frontmatter, and content structure."

Using this skill:

- Ensures your `description` field contains effective trigger phrases.
- Catches common mistakes (missing fields, weak descriptions, wrong folder)
  before CI does.
- Produces a consistent style across all skills in the repository.

> **This step is strongly recommended.** Pull requests that skip it often
> require multiple review rounds to fix frontmatter and description quality
> issues that the skill catches automatically.

---

## Step 2 — Choose the Right Location

Skills are organised into top-level categories under `skills/`:

| Folder | Use for |
|---|---|
| `skills/meta/` | Skills about authoring or managing other skills |
| `skills/products/<product>/` | Tightly scoped to one Canonical product |
| `skills/engineering/` | Cross-product engineering practices |
| `skills/documentation/` | Cross-product documentation standards |
| `skills/practices/` | Cross-functional ways of working (planning, delivery, retrospectives) |
| `skills/operations/` | Infrastructure, deployment, operational runbooks |
| `skills/security/` | Security practices, compliance workflows |

**Decision rule:** if a skill applies to more than one Canonical product
without modification, place it in an expertise category, not `products/`.

### Product sub-folders

For product skills, create (or reuse) a product sub-folder:

```text
skills/products/
└── juju/                    ← product sub-folder
    └── juju-charm-authoring/ ← your skill folder
        └── SKILL.md
```

If a new product sub-folder is needed, add a corresponding CODEOWNERS entry
(see [CODEOWNERS](CODEOWNERS)).

---

## Step 3 — Create Your Skill

Create a folder whose name matches your skill's `name` field exactly. Every
skill folder must contain exactly one `SKILL.md` file.

### Minimum structure

```text
skills/<category>/<skill-name>/
└── SKILL.md
```

### With reference documents (for complex, multi-topic skills)

```text
skills/<category>/<skill-name>/
├── SKILL.md
└── references/
    ├── topic-a.md
    └── topic-b.md
```

Use the `references/` pattern when the skill body would exceed roughly 200
lines or covers more than three distinct sub-topics. The main `SKILL.md` acts
as a router that directs the agent to the right reference based on trigger
keywords (see `skills/meta/generate-agent-skills/SKILL.md` for an example).

---

## Step 4 — Write the Frontmatter

Every `SKILL.md` must begin with a YAML frontmatter block. All fields below
are required unless marked optional.

```yaml
---
name: <kebab-case-skill-name>          # must match folder name exactly
description: >
  <What the skill does in 1–2 sentences.>
  <Depth of guidance it provides.>
  WHEN: <comma-separated activation trigger keywords — at least 8 phrases>.
license: Apache-2.0
metadata:                              # per agentskills.io spec, extra fields go here
  author: Canonical             # or Canonical/<team>, e.g. Canonical/platform-engineering
  version: "1.0.0"                     # SemVer, quoted
  summary: One or two sentence human-readable blurb shown on skill cards (≤ 160 chars).
  tags:                                # at least one tag
    - <product or domain>
    - <secondary tag>                  # optional
---
```

### The `description` field

The `description` is the **only field agents read at discovery time.** It
determines whether the agent activates this skill for a given task.

A strong description:

- Is at least 20 words before the `WHEN:` clause.
- Includes a `WHEN:` clause with 8 or more distinct trigger phrases covering
  both beginner and expert vocabulary.
- Contains no tool-specific or Copilot-specific references.

Example:

```yaml
description: >
  Guides authoring production-ready Juju charms using the Ops library.
  Covers charm structure, event handling, relation interfaces, config schemas,
  and testing with the Harness and state-transition frameworks.
  WHEN: create charm, juju operator, ops library, charm events, juju relation,
  charm config, charm testing, harness test, state transition test, ops framework.
```

### Frontmatter field reference

| Field | Type | Rule |
|---|---|---|
| `name` | string | lowercase kebab-case; may start with a digit (e.g. `12factor-app`); unique; matches folder name |
| `description` | block scalar | ≥ 20 words + `WHEN:` clause |
| `license` | string | Must be `Apache-2.0` |
| `metadata.author` | string | Must start with `Canonical` (e.g. `Canonical` or `Canonical/platform-engineering`) |
| `metadata.version` | string | SemVer `"X.Y.Z"` — must be quoted |
| `metadata.summary` | string | ≤ 160 chars — shown on skill cards; falls back to truncated `description` if absent |
| `metadata.tags` | list | At least one entry (recommended) |

> These fields follow the [agentskills.io specification](https://agentskills.io/specification):
> `license` is a standard top-level field; `author`, `version`, and `tags` live under
> the spec-standard `metadata:` mapping.

---

## Step 5 — Validate Locally

Run all validations with a single command:

```bash
make check
```

Or run individual checks:

```bash
make validate   # frontmatter, name uniqueness, description quality
make lint       # markdown formatting
make pages      # smoke-test the page generator
```

`make validate` checks:

- Required fields are present and non-empty: `name`, `description`, `license` (top-level);
  `metadata.author`, `metadata.version` (under `metadata:`).
- `name` is lowercase kebab-case and unique across the repo.
- `name` matches the skill's folder name.
- `metadata.version` follows SemVer.
- `metadata.author` starts with `Canonical` (e.g. `Canonical` or `Canonical/platform-engineering`) and `license` is `Apache-2.0`.
- `metadata.summary` is ≤ 160 characters (warning only).
- `description` has adequate length and trigger phrases (warnings).
- Each skill directory contains exactly one `SKILL.md`.

Fix all **errors** before opening a PR. **Warnings** are advisory — address
them if you can, but they will not block a merge.

---

## Step 6 — Open a Pull Request

1. Fork the repository and create a branch.
2. Add your skill folder.
3. Run `python scripts/validate_skills.py` — must exit 0.
4. Push and open a PR against `main`.

### PR checklist

- [ ] `validate_skills.py` exits 0 (no errors)
- [ ] Markdown lint passes
- [ ] Skill folder name matches the `name` frontmatter field
- [ ] Skill is in the correct category folder
- [ ] You have tested the skill by installing it locally and activating it with
      your agent on a representative task
- [ ] CODEOWNERS updated if a team other than Platform Engineering owns this skill

### What reviewers check

- The `description` accurately describes what the skill does and triggers
  correctly on realistic user requests.
- The body content is correct, clear, and free of tool-specific assumptions.
- The skill does not duplicate an existing skill; if overlap exists, the PR
  includes a proposal for consolidation or differentiation.

---

## Updating an Existing Skill

1. Make your changes.
2. Bump the `version` field (patch for corrections, minor for additions,
   major for breaking changes to the skill's interface).
3. Run the same validation steps as above.
4. Open a PR — the CODEOWNER for that folder must review.

---

## Questions and Feedback

- Open an issue for bug reports, inaccuracies, or skill requests.
- Suggest new categories or structural changes via an issue before opening a PR
  — design decisions benefit from discussion.
