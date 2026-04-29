---
name: confdb
description: >
  Guides migration and implementation of snapd ConfDB (configuration database)
  for custodian and observer snaps. ConfDB follows a custodian–observer pattern
  where custodian snaps write configuration to a central validated store and
  observer snaps read it via controlled views, with access governed by interface
  permissions for isolation and type safety. This skill covers: designing confdb
  schemas and views for multi-snap systems, checking schema and plug naming
  convention compliance and suggesting exact renames, implementing custodian and
  observer snap hooks correctly including configure, change-view, and
  observe-view hooks, avoiding common pitfalls such as deadlocks from confdb
  access inside connect hooks, signing keys and assertion import/signing
  workflow, interface connection sequencing, writing unit and integration tests
  for confdb-enabled snaps, migrating existing file-based or legacy
  configuration to confdb, planning hybrid backward-compatible rollout
  strategies, and troubleshooting connection, permission, and initialisation
  failures across multi-snap systems.
  WHEN: migrate snap configuration to confdb, migrate file-based configuration to confdb, design a confdb schema, share configuration between snaps, share network configuration between snaps, single source of truth for snap configuration, define admin and state views, check confdb naming conventions, review snapcraft.yaml plugs for confdb, do my views and plug names follow naming guidelines, suggest renames to make confdb naming-compliant, implement configure hook writes, implement change-view hooks, implement observe-view hooks, avoid connect hook deadlocks, observer snap deadlock when connecting interface, troubleshoot confdb interface connection failures, debug no custodian snap connected errors, debug view not found errors, validate storage path version prefixes, sign and import confdb-schema assertions, write unit tests for confdb hooks, write integration tests for confdb custodian snap, plan hybrid backward-compatible content-slot rollout, review confdb migration pull requests.
license: Apache-2.0
metadata:
  author: Canonical
  version: "1.1.0"
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

- [Migration Playbook](./CONFDB_MIGRATION_GUIDE.md) — step-by-step migration workflow, hybrid/backward-compatibility rollout, and links to all reference docs
- [Naming Conventions](./CONFDB_NAMING_CONVENTIONS.md) — rules and compliance checklist for schema names, view names, plug names, and storage paths

## Detailed Reference Docs

- [Concepts](./CONFDB_CONCEPTS.md) — what confdb is, custodian/observer pattern, connection order
- [Getting Started](./CONFDB_GETTING_STARTED.md) — enabling the feature, signing keys, schema import
- [Schema Design](./CONFDB_SCHEMA_DESIGN.md) — schema structure, views, defaults files, versioning/evolution
- [Hook Patterns](./CONFDB_HOOKS.md) — configure hook, connect hook, reading config, pitfalls with code examples
- [Testing](./CONFDB_TESTING.md) — unit tests, integration tests, snapctl-wrapper helper
- [Troubleshooting](./CONFDB_TROUBLESHOOTING.md) — diagnosing errors, debugging commands, best practices