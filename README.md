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

- **Install the `generate-agent-skills` skill first** — it guides your agent
  through purpose scoping, frontmatter authoring, trigger phrases, and the
  pre-submission checklist, producing higher-quality, consistent skills:

  ```bash
  npx skills add canonical/skills --skill generate-agent-skills
  ```

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
