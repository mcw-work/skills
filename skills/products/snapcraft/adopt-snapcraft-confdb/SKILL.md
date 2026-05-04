---
name: adopt-snapcraft-confdb
description: >
  Guides adoption of snapd ConfDB for Snap ecosystems using the
  custodian-observer model. Explains when to use ConfDB, how to design schemas
  and views, how to apply naming conventions, and how to sign and import
  confdb-schema assertions. Includes safe hook patterns for configure,
  change-view, and observe-view, migration from file/content-slot
  configuration with staged compatibility, unit and integration testing
  strategies, and troubleshooting for connection, permission, and
  initialization failures.
  WHEN: migrate snap configuration to confdb, design confdb schema, define
  admin and state views, check confdb naming conventions, implement configure
  hook writes, implement change-view validation, implement observe-view
  reactions, sign and import confdb-schema assertions, test confdb-enabled
  snaps, troubleshoot confdb interface failures, plan hybrid backward-compatible
  rollout, review confdb migration pull requests.
license: Apache-2.0
metadata:
  author: Canonical
  version: "1.1.2"
  summary: Guidance for adopting and operating ConfDB in snaps with schema design, naming, hooks, testing, migration, and troubleshooting support.
  tags:
    - snaps
    - snapd
    - confdb
    - configuration
    - migration
---

Use the documents in this skill to help developers adopt confdb in their snaps.

## What is ConfDB?

ConfDB (configuration database) is a snapd feature that allows snaps to share
structured, validated configuration data. It follows a **custodian–observer**
pattern:

- **Custodian snaps** write configuration to a central store, validated against
  a JSON schema.
- **Observer snaps** read that configuration via controlled views.
- Access is governed by interface permissions, providing isolation and type
  safety.

ConfDB is suited to multi-snap systems where a single source of truth for
configuration is needed. For single-snap configuration, standard `snap config`
remains the appropriate choice.

## Primary References

- [Migration Playbook](./references/CONFDB_MIGRATION_GUIDE.md) — step-by-step migration workflow, hybrid/backward-compatibility rollout, and links to all reference docs
- [Naming Conventions](./references/CONFDB_NAMING_CONVENTIONS.md) — rules and compliance checklist for schema names, view names, plug names, and storage paths

## Detailed Reference Docs

- [Concepts](./references/CONFDB_CONCEPTS.md) — what confdb is, custodian/observer pattern, connection order
- [Getting Started](./references/CONFDB_GETTING_STARTED.md) — enabling the feature, signing keys, schema import
- [Schema Design](./references/CONFDB_SCHEMA_DESIGN.md) — schema structure, views, defaults files, versioning/evolution
- [Scripts Guide](./references/CONFDB_SCRIPTS_GUIDE.md) — local schema development with helper utilities from `scripts/` folder
- [Hook Patterns](./references/CONFDB_HOOKS.md) — configure hook, connect hook, reading config, pitfalls with code examples
- [Testing](./references/CONFDB_TESTING.md) — unit tests, integration tests, snapctl-wrapper helper
- [Troubleshooting](./references/CONFDB_TROUBLESHOOTING.md) — diagnosing errors, debugging commands, best practices