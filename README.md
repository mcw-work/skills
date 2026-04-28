<!--
  Copyright 2026 Canonical Ltd.
  See LICENSE file for licensing details.
-->

# Canonical Skills

[![Install via skills CLI](https://img.shields.io/badge/skills.sh-install-green)](https://skills.sh/canonical/skills)
[![Validate Skills](https://github.com/canonical/skills/actions/workflows/validate.yml/badge.svg)](https://github.com/canonical/skills/actions/workflows/validate.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)

Agent Skills for Canonical products and technologies — works with any
[skills-compatible agent](https://agentskills.io/clients) (GitHub Copilot CLI,
Claude Code, Cursor, Codex, Gemini CLI, Windsurf, and more).

## Installation

Install all skills from this repository:

```bash
npx skills add canonical/skills
```

Install a specific skill by name:

```bash
npx skills add canonical/skills --skill <skill-name>
```

## Available Skills

Full listing with search and filtering: [canonical.github.io/skills](https://canonical.github.io/skills)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for a step-by-step guide. Key points:

- **Use a skill authoring tool first** — ask your agent to help you author the
  skill before writing manually; it will guide you through trigger phrases,
  frontmatter, and content structure.
- Validate locally with `make check` before pushing.
- Each skill lives in its own folder under `skills/<category>/<skill-name>/`
  and contains exactly one `SKILL.md`.

## Support

Open an [issue](https://github.com/canonical/skills/issues) to:

- Report inaccuracies or bugs in a skill.
- Request a new skill for a Canonical product or technology.
- Propose structural or governance changes.

## License

Apache 2.0 — see [LICENSE](LICENSE).
