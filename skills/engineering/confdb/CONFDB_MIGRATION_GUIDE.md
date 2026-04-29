# Confdb Migration Playbook

This playbook walks through migrating a snap (or a set of snaps) to confdb. It is the recommended starting point — follow the steps in order, using the linked reference documents for implementation details.

## Pre-Migration Checklist

Before you start, confirm:

- [ ] `experimental.confdb=true` is set on your dev system ([Getting Started](./CONFDB_GETTING_STARTED.md))
- [ ] You have a Snap Store account with a registered signing key
- [ ] You understand whether you need backward compatibility with file-based or content-slot consumers (see [Hybrid Rollout](#hybrid-rollout-backward-compatibility) below)
- [ ] You have reviewed the naming conventions ([CONFDB_NAMING_CONVENTIONS.md](./CONFDB_NAMING_CONVENTIONS.md))

---

## Step 1 — Design Your Schema

Decide on:
- Which snaps are custodians (write) and which are observers (read)
- What configuration fields are needed and their types (`string`, `int`, `bool`)
- Which views to expose and at what access level (`read-write` vs `read`)
- Whether to version storage paths (strongly recommended — see [Schema Evolution](./CONFDB_SCHEMA_DESIGN.md#schema-evolution))

→ See [CONFDB_SCHEMA_DESIGN.md](./CONFDB_SCHEMA_DESIGN.md) for schema structure, view design, defaults files, and versioning guidance.

→ See [CONFDB_NAMING_CONVENTIONS.md](./CONFDB_NAMING_CONVENTIONS.md) to validate your schema names, view names, and plug names before signing.

**Exit criteria:** Schema YAML written and reviewed for naming compliance.

---

## Step 2 — Sign and Import the Schema

Convert, sign, and import your schema as a `confdb-schema` assertion.

→ See [CONFDB_GETTING_STARTED.md](./CONFDB_GETTING_STARTED.md) for key creation and the sign-and-import workflow.

**Exit criteria:** `snap known confdb-schema` returns your schema.

---

## Step 3 — Implement the Custodian Snap

1. Add confdb plugs to `snapcraft.yaml` — include `role: custodian` on the write plug
2. Create a defaults file with placeholder values
3. Implement the `configure` hook: validate completeness, replace placeholders, write to confdb
4. Implement the `change-view-<plug>` hook: validate incoming writes from any snap

→ See [CONFDB_HOOKS.md](./CONFDB_HOOKS.md) for the configure and change-view hook patterns, critical rules, and pitfalls.

**Exit criteria:** Running `snap set my-config-snap field-one=value` writes to confdb and `snapctl get :my-app-admin --view -d` returns the value.

---

## Step 4 — Connect the Custodian

```bash
sudo snap connect my-config-snap:my-app-admin   # plug with role: custodian
sudo snap connect my-config-snap:my-app-state   # read-only plug (optional, for self-observation)
```

**Exit criteria:** `snap connections my-config-snap | grep confdb` shows the admin plug connected; a `snap set` triggers a successful write.

---

## Step 5 — Implement Observer Snaps

1. Add the state (read-only) confdb plug to `snapcraft.yaml`
2. Implement `connect-plug-<name>` hook: log the connection, restart affected services (do **not** access confdb here)
3. Implement `observe-view-<name>` hook: read updated values and reload services when data changes
4. Implement config reading in application code using `snapctl get :plug-name --view`

→ See [CONFDB_HOOKS.md](./CONFDB_HOOKS.md) for the observer connect hook, observe-view hook pattern, and the `confdb_utils.py` reading utility.

**Exit criteria:** Observer snap connects, services restart, and config values are read correctly.

---

## Step 6 — Test

Write unit tests (mock `snapctl` and filesystem) and integration tests (gated behind `RUN_INTEGRATION_TESTS=1`).

→ See [CONFDB_TESTING.md](./CONFDB_TESTING.md) for unit test patterns, the `snapctl-wrapper` integration test helper, and test helpers.

**Exit criteria:** Unit tests pass without a snap environment; integration tests pass with a real snap install.

---

## Hybrid Rollout (Backward Compatibility)

If you have existing consumers that depend on file-based or content-slot configuration, you can run confdb alongside the legacy mechanism during a transition period.

**Pattern:** The custodian snap exposes both a confdb view **and** a content slot. Its configure hook updates both.

**snapcraft.yaml additions:**
```yaml
slots:
  configuration-read:
    interface: content
    read:
      - $SNAP_COMMON/configuration

hooks:
  configure:
    plugs: [my-app-admin]
```

**Configure hook responsibility:**
1. Validate all required config values are present
2. Write to confdb (primary)
3. Sync files under `$SNAP_COMMON/configuration/` for content-slot consumers

→ See the file-sync script pattern in [CONFDB_HOOKS.md](./CONFDB_HOOKS.md#updating-file-based-config-content-slot-compatibility).

### Rollout and Cutover Sequence

1. **Deploy custodian** with both confdb plugs and content slot
2. **Migrate new observers** to use confdb (connect the state plug)
3. **Keep legacy consumers** connected to the content slot while they migrate
4. **Verify** all consumers are reading from confdb correctly
5. **Remove the content slot** from the custodian and disconnect legacy consumers
6. **Remove** the file-sync code from the configure hook

Do not remove the content slot until all consumers have migrated — removing it disconnects them immediately.

---

## Reference Documents

| Document | Purpose |
|----------|---------|
| [CONFDB_CONCEPTS.md](./CONFDB_CONCEPTS.md) | What confdb is, custodian/observer pattern, connection order |
| [CONFDB_GETTING_STARTED.md](./CONFDB_GETTING_STARTED.md) | Enabling confdb, signing keys, schema import |
| [CONFDB_SCHEMA_DESIGN.md](./CONFDB_SCHEMA_DESIGN.md) | Schema structure, views, defaults, evolution/versioning |
| [CONFDB_NAMING_CONVENTIONS.md](./CONFDB_NAMING_CONVENTIONS.md) | Naming rules and compliance checklist |
| [CONFDB_HOOKS.md](./CONFDB_HOOKS.md) | Hook patterns, critical rules, pitfalls, code examples |
| [CONFDB_TESTING.md](./CONFDB_TESTING.md) | Unit and integration testing strategies |
| [CONFDB_TROUBLESHOOTING.md](./CONFDB_TROUBLESHOOTING.md) | Diagnosing errors, debugging commands, best practices |

---

## Further Reading

- [Snapd Confdb Documentation](https://snapcraft.io/docs/confdb)
- [Interface Management](https://snapcraft.io/docs/interface-management)
- [Supported Snap Hooks](https://snapcraft.io/docs/supported-snap-hooks)
