# Confdb Concepts

## What is Confdb?

Confdb is snapd's configuration database feature. It lets snaps share structured, validated configuration data through a central store. Configuration is defined in a JSON schema, access is controlled through interface permissions, and values are distributed to consumer snaps via named views.

Confdb follows a **custodian–observer** pattern:

| Role | Responsibility |
|------|----------------|
| **Custodian** | Has `role: custodian` on its plug; its `change-view` hook validates every write to the view |
| **Writer** | Any snap with a read-write plug can write; at least one custodian must be connected |
| **Observer** | Reads configuration from confdb via a read-only or read-write view; reacts via `observe-view` hook |

## When to Use Confdb

✅ **Good use cases:**
- Multiple snaps need to share configuration
- Configuration needs validation and type safety
- You want a single source of truth for config
- Observer snaps should react to configuration changes

❌ **Not ideal for:**
- Single-snap configuration (use `snap config`)
- Unstructured or highly dynamic data
- Snaps that need to function without confdb support in the field

## Core Principle: Confdb-First Architecture

**Confdb is the single source of truth for configuration.** Files written to disk are derived outputs only, used for:

1. **Initialization defaults** — checked into your repo under a `defaults/` folder, containing placeholder values that are replaced at configure time
2. **Live runtime configuration** — generated from confdb values when a service needs a file-based config

Never treat files as the primary source and sync _into_ confdb from them.

## Custodian Pattern

The custodian snap is the **write validator** for a view. Any snap with a read-write plug can write to confdb, but at least one snap with `role: custodian` must be connected — its `change-view-<plug>` hook runs on every write and can validate, modify, or reject the transaction.

The custodian typically also performs the initial write (via its `configure` hook), making it the de-facto config manager in most deployments.

**snapcraft.yaml excerpt:**
```yaml
plugs:
  my-app-admin:
    interface: confdb
    account: YOUR_ACCOUNT_ID
    view: my-app/admin
    role: custodian    # required to run change-view hook and gate all writes

  my-app-state:
    interface: confdb
    account: YOUR_ACCOUNT_ID
    view: my-app/state

hooks:
  configure:
    plugs: [my-app-admin]
  change-view-my-app-admin:
    plugs: [my-app-admin]
```

The `configure` hook reads values from `snap set`, validates completeness, and writes to confdb. The `change-view-my-app-admin` hook validates every write to the view, including those from other snaps.

## Observer Pattern

Observer snaps connect a confdb plug (typically read-only) and react to configuration changes using two hooks:

- **`connect-plug-<name>`** — fires when the interface is first connected; restart services here so they pick up the initial config on next read. Must not access confdb.
- **`observe-view-<name>`** — fires after each committed write to the view, for every connected snap except the one that made the write. Use `snapctl get :plug-name --view` here. Errors in this hook are ignored by snapd.

**snapcraft.yaml excerpt:**
```yaml
plugs:
  my-app-state:
    interface: confdb
    account: YOUR_ACCOUNT_ID
    view: my-app/state

hooks:
  connect-plug-my-app-state:
    plugs: [my-app-state]
  observe-view-my-app-state:
    plugs: [my-app-state]
```

## Connection Order

Confdb must be initialised before observers can access data:

1. Import the `confdb-schema` assertion (`sudo snap ack schema.assert`)
2. Install the **custodian** snap (the snap with `role: custodian` on its plug)
3. Connect the custodian's plugs
4. Configure the custodian snap via `snap set` — this writes the initial values to confdb
5. Install and connect **observer** snaps

If no snap with `role: custodian` is connected when a write is attempted, snapd will reject it with `"cannot commit changes to confdb: no custodian snap connected"`.
