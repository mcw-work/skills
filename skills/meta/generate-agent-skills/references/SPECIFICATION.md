# Agent Skill Technical Specification

## 1. Directory Naming Constraints (The Semantic Anchor)
The root directory identifies the skill and serves as the primary routing key.
* **Regex:** `^[a-z0-9][a-z0-9-]*[a-z0-9]$`
* **Constraint:** Lowercase, alphanumeric (`a-z`, `0-9`), and hyphens (`-`) only.
* **Length:** Max 64 characters.

## 2. File Structure & Roles
The filesystem uses a "Progressive Disclosure" hierarchy. Only `SKILL.md` is strictly mandatory.

| Path | Type | Requirement | Role |
| :--- | :--- | :--- | :--- |
| `SKILL.md` | File | **Mandatory** | The "Orchestrator". Contains metadata and routing logic. |
| `references/` | Directory | **Optional** | "Base Knowledge". Storage for static files (PDFs, JSON, CSV). |
| `scripts/` | Directory | **Optional** | "Executable Knowledge". Storage for code (Python, Bash). |
| `assets/` | Directory | **Optional** | Non-functional resources (images, raw templates). |

## 3. Metadata Specification (YAML Frontmatter)
The `SKILL.md` file must begin with a YAML block. The structure follows the
[agentskills.io specification](https://agentskills.io/specification#metadata-field):
`license` is a standard top-level field; `author`, `version`, and `tags` are stored
under the spec-standard `metadata:` mapping.

| Field | Required | Description |
| :--- | :--- | :--- |
| `name` | **Yes** | Must match the root directory name exactly. |
| `description` | **Yes** | Max 1024 chars. 3rd person. Must include a `WHEN:` clause with 8+ trigger phrases. |
| `license` | **Yes** (this repo) | Top-level. SPDX identifier, e.g. `Apache-2.0`. |
| `metadata.version` | **Yes** (this repo) | Under `metadata:`. SemVer string, e.g. `"1.0.0"`. Bump on every change. |
| `metadata.author` | **Yes** (this repo) | Under `metadata:`. Your organization or team name. |
| `metadata.summary` | Recommended | Under `metadata:`. ≤ 160 chars. Human-readable blurb shown on skill cards; falls back to truncated `description` if absent. |
| `metadata.tags` | Recommended | Under `metadata:`. List of domain or product keywords. |

**Correct example:**
```yaml
---
name: my-skill
description: >
  Does something useful. WHEN: trigger1, trigger2, trigger3, ...
license: Apache-2.0
metadata:
  author: your-org
  version: "1.0.0"
  summary: One sentence shown on skill cards (≤ 160 chars).
  tags:
    - domain
---
```

## 4. The Progressive Disclosure Pattern
Structure your skill based on complexity.

### Type A: Pure Prompt Skill (Simple)
* **Use Case:** Summarization, simple tasks.
* **Structure:**
    ```text
    my-simple-skill/
    └── SKILL.md
    ```

### Type B: Tool-Backed Skill (Complex)
* **Use Case:** Data processing, API interaction, file manipulation.
* **Structure:**
    ```text
    my-complex-skill/
    ├── SKILL.md
    ├── references/   # Schema definitions
    └── scripts/      # Python logic
    ```