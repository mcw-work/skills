# Confdb Naming Convention Guide

This guide defines naming conventions for confdb schema design and provides a practical checklist for validating schema consistency.

Use this guide when reviewing or generating:
- confdb schema names
- view names
- confdb interface plug names
- request paths
- storage paths

## Purpose

Consistent naming makes confdb-schema assertions easier to read, safer to evolve, and simpler to maintain across teams.

## Core Rules

### 1. View Names

View names should answer: "What access or control do I get if I have this view?"

Preferred pattern:
- `<noun>-admin` for control/write access
- `<noun>-state` for read-only access

Recommended designations:
- `X-admin`
- `X-state`

Guidance:
- Use clear nouns that scope what is being controlled or observed.
- Favor short names.
- Avoid redundant suffix words like `configuration`, `settings`, or `status` when already implied by the view role.
- In tightly scoped schemas, bare `admin` or `state` may be acceptable if the schema context is already unambiguous.

Examples:
- Good: `wifi-admin`, `wifi-state`, `pinning-admin`
- Acceptable in constrained schema: `admin`, `state`
- Avoid: `wifi-configuration-admin`, `network-settings-state`

### 2. Schema Names

Schema names should be descriptive, concise nouns that reflect domain intent.

Guidance:
- Keep names short and specific.
- Avoid redundant words such as `configuration`, `settings`, or `status`.

Examples:
- Good: `validation-sets`, `network`
- Avoid: `network-configuration`, `validation-set-status`

### 3. Interface Plug Names

Use this pattern for confdb interface plugs:
- `<schema>-<view-name>`

Optional prefix when needed for clarity:
- `<account>-<schema>-<view-name>`

Examples:
- `validation-sets-state`
- `validation-sets-pinning-admin`
- `system-validation-sets-state` (only when extra scoping clarity is required)

### 4. Request Paths

Request paths represent the virtual request document exposed by the schema.

Guidance:
- Use dot-separated hierarchy for parent/child objects.
- Use plural nouns for collection/group keys.
- Request structure may differ from storage structure, but mapping must remain clear and intentional.

Examples:
- Good: `device.metadata.id`, `interfaces.{name}`, `tunnel.peers`
- Avoid: ambiguous flat keys when hierarchy is intended

### 5. Storage Paths

Storage paths should start with a literal, versioned prefix to support schema evolution.

Preferred pattern:
- `v<version>.<...>` (for example `v1.<...>`)

Guidance:
- Begin with a non-placeholder literal prefix.
- Keep prefixes aligned with the top-level storage schema shape.
- Preserve compatibility by introducing new version prefixes for layout changes.

Examples:
- Good: `v1.{account}.{validation-set}`
- Avoid: `{account}.{validation-set}` as the root (no evolution prefix)

## Compliance Checklist

Use this checklist to validate a schema quickly.

### Views
- [ ] Each view name clearly communicates capability.
- [ ] Read-only views use `-state` (or justified constrained equivalent).
- [ ] Write/control views use `-admin` (or justified constrained equivalent).
- [ ] View nouns are specific and not overly broad.
- [ ] No unnecessary words like `configuration`, `settings`, `status`.

### Schema
- [ ] Schema name is concise and domain-specific.
- [ ] Schema name avoids redundant suffixes.

### Interface plugs
- [ ] Plug names follow `<schema>-<view-name>`.
- [ ] Optional account/project prefix is used only when needed.
- [ ] Plug name, `account`, and `view` fields are semantically aligned.

### Request paths
- [ ] Dot notation is used for hierarchy where appropriate.
- [ ] Collection keys are pluralized nouns.
- [ ] Request path naming is readable and consistent across rules.

### Storage paths
- [ ] Every storage path starts with a literal version prefix (for example `v1`).
- [ ] Storage path prefixes align with the storage schema's top-level structure.
- [ ] Versioning strategy supports backward compatibility.

## Review Prompt Template

Use this prompt with an AI reviewer:

"Review this confdb schema for naming-convention compliance using the Confdb Naming Convention Guide. Check schema name, view names, interface plug names, request paths, and storage paths. Return:
1. pass/fail per rule section,
2. specific violations,
3. exact rename suggestions,
4. any justified exceptions (for constrained schemas using bare `admin` or `state`)."

## Exception Handling

An exception is acceptable only when:
- schema context is already tightly constrained,
- the shorter name improves clarity,
- and the exception does not broaden implied permissions.

Document exceptions explicitly in schema comments or review notes.