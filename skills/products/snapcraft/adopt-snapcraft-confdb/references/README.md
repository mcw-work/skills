# References

This directory contains supplemental reference material for the confdb skill.

## How to Use This Folder

- `../SKILL.md` is the main entry point and router for the skill
- Reference documents below are linked from `SKILL.md` and from each other
- `CONFDB_SCRIPTS_GUIDE.md` explains the helper scripts in `../scripts/` for local development
- All other documents follow the [CONFDB_MIGRATION_GUIDE.md](./CONFDB_MIGRATION_GUIDE.md) workflow

## Reference Documents

### Core Concepts & Design
- `CONFDB_CONCEPTS.md` — What confdb is, custodian/observer pattern, connection order
- `CONFDB_SCHEMA_DESIGN.md` — Schema structure, views, defaults files, versioning/evolution
- `CONFDB_NAMING_CONVENTIONS.md` — Naming rules and compliance checklist

### Getting Started & Workflows
- `CONFDB_GETTING_STARTED.md` — Enabling confdb, signing keys, manual schema import
- `CONFDB_MIGRATION_GUIDE.md` — Step-by-step migration workflow (recommended starting point)
- `CONFDB_SCRIPTS_GUIDE.md` — Using helper scripts for local schema development

### Implementation Guides
- `CONFDB_HOOKS.md` — Hook patterns, critical rules, pitfalls, code examples
- `CONFDB_TESTING.md` — Unit and integration testing strategies

### Troubleshooting
- `CONFDB_TROUBLESHOOTING.md` — Diagnosing errors, debugging commands, best practices
