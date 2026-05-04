# ConfDB Scripts Guide

This guide explains how to use the helper scripts in the `scripts/` folder when developing confdb schemas for snaps. These scripts enable **local** schema editing, signing, and testing without uploading to the Snap Store on every iteration.

## Why These Scripts?

By default, `snapcraft edit-confdb-schema` immediately uploads your changes to the Snap Store. During development, this is cumbersome because:

- ❌ Each schema change requires store authentication and upload
- ❌ Can't easily test multiple versions locally
- ❌ Hard to collaborate on schema changes (no version control workflow)
- ❌ Revision number management is manual and error-prone

These scripts solve this by keeping your schema **local** during development:

- ✅ Edit, sign, and test locally without store interaction
- ✅ Version schemas in git and import pre-reviewed versions
- ✅ Automatic revision bumping during iterations
- ✅ Familiar `snap ack` workflow for local schema installation

## Quick Start: 60-Second Example

```bash
# Terminal 1: Start editing with snapcraft
EDITOR=./snapcraft-hold-editor \
  snapcraft edit-confdb-schema $ACCOUNT_ID $SCHEMA_NAME

# Terminal 2: Edit the file while Terminal 1 waits
vim ~/.snapcraft-hold/confdb-schema-edit.yaml

# Terminal 2: Sign and acknowledge locally
./snapcraft-sign-and-ack -k my-signing-key

# Terminal 1: Press Enter to close snapcraft
# (snapcraft will try to upload, but your local schema is already installed via snap ack)

# Verify the schema is ready
snap known confdb-schema name=$SCHEMA_NAME | head -5
```

## Scripts and Their Roles

### snapcraft-hold-editor

**What it does:** Intercepts snapcraft's temporary editor window, saves your schema to a persistent file, and lets you edit it with your own tools.

**When to use:**
- You want to edit the schema using your preferred editor (Vim, VS Code, etc.)
- You're iterating quickly and want to sign/test without touching snapcraft

**How it works (technical):**
1. Snapcraft calls `$EDITOR` (which is set to this script)
2. Script saves the temp file to `~/.snapcraft-hold/confdb-schema-edit.yaml`
3. Script waits and displays instructions
4. You edit the file in another terminal
5. You press Enter in the first terminal to continue
6. Script copies the edited file back to snapcraft's temp location

**Environment variables:**
- `REAL_EDITOR` - Optional editor to launch automatically (e.g., `vim`, `code`, `subl`)
- `SNAPCRAFT_HOLD_DIR` - Override where files are saved (default: `~/.snapcraft-hold`)

### snapcraft-import-editor

**What it does:** Replaces snapcraft's schema with a YAML file from your filesystem (e.g., from git).

**When to use:**
- You have schema versions in version control
- You want to apply a reviewed schema from a peer
- You need to test a pre-prepared schema variant

**How it works (technical):**
1. Snapcraft calls `$EDITOR` (which is set to this script)
2. Script prompts you to enter a file path
3. Script shows a unified diff (old vs. new) in `less`
4. You confirm the import
5. Script copies the file to snapcraft's temp location

**Diff inspection:**
- The diff shows exactly what will change
- Compare metadata (account-id, name, revision) at a glance
- Press 'q' to exit the diff viewer

### snapcraft-sign-and-ack

**What it does:** Converts, signs, and installs a confdb schema into snapd **locally** without uploading to the store.

**When to use:**
- After editing with `snapcraft-hold-editor`, to sign and install the schema
- When you have a YAML file and want to test it locally
- To push a new revision into your local snapd for observer testing

**Key features:**
- **Auto-bumps revision** (recommended) — each sign-and-ack increments the revision, so new observers see the update
- **Uses your local signing key** — no store authentication needed
- **Automatic YAML-to-JSON conversion** — you don't manage JSON manually
- **Atomic workflow** — one command converts → signs → acknowledges

**Revision bumping explained:**

By default, the script auto-bumps the revision (e.g., 5 → 6). This is **correct behavior** for development because:

| Scenario | Auto-bump | Result |
|----------|-----------|---------|
| First sign-and-ack after editing | Yes (recommended) | Observers see the new schema |
| Rapid iteration (edit many times) | Yes (each iteration bumps) | Each test gets a new version number |
| Testing same schema locally | Yes | Fine; local snapd accepts it |
| Importing reviewed schema | Yes (default) | Updates to the new version |

**When to use `--no-bump`:**
- Rare edge case: you want to test a schema without changing its revision
- Importing a pre-signed schema that you want to keep at a specific revision
- Debugging why a particular revision number causes issues

**Examples:**

```bash
# Standard workflow: edit + sign with auto-bump
EDITOR=./snapcraft-hold-editor snapcraft edit-confdb-schema $ACCOUNT $NAME
./snapcraft-sign-and-ack -k my-key
# Revision automatically incremented; observers will see the new schema

# Sign a specific file
./snapcraft-sign-and-ack -k my-key ~/my-schemas/network-v7.yaml

# Without bumping (rare)
./snapcraft-sign-and-ack -k my-key --no-bump schema.yaml

# Preview what will happen (don't execute)
./snapcraft-sign-and-ack -k my-key --dry-run
```

### yaml-to-sign-json.py

**What it does:** Converts YAML confdb schema to JSON format (required by `snap sign`).

**When to use:**
- You're using `snapcraft-sign-and-ack` (it calls this automatically)
- Manual workflow: you want to control each signing step
- Debugging schema conversion issues

**What it handles:**
- Adds missing required fields (`type`, `authority-id`, `timestamp`)
- Ensures correct field types for `snap sign`
- Properly formats the `body` field
- Removes fields that `snap sign` will add

**Manual example:**
```bash
# If you want to inspect the JSON before signing
./yaml-to-sign-json.py schema.yaml > schema.json
cat schema.json | jq .
```

## Common Workflows

### Workflow 1: Rapid Schema Development

**Goal:** Edit schema → test with observers → repeat quickly

```bash
# Terminal 1: Start editing with snapcraft
EDITOR=./snapcraft-hold-editor \
  snapcraft edit-confdb-schema $ACCOUNT_ID $SCHEMA_NAME

# Terminal 2: Edit the file
vim ~/.snapcraft-hold/confdb-schema-edit.yaml

# Terminal 2: Sign and install locally
./snapcraft-sign-and-ack -k my-key

# Terminal 1: Press Enter to continue (snapcraft tries to upload, abort with Ctrl+C)

# Test with observer snaps (installed and connected)
snap set my-custodian-snap field-one=value
# Observe that observer snaps react (observe-view hooks fire)

# Repeat: Terminal 2, edit the file again, sign-and-ack, test
```

**Why this works:**
- Each `snapcraft-sign-and-ack` bumps the revision
- Observer snaps see the new revision and react
- No store upload or authentication needed
- Can iterate 20+ times in an afternoon

### Workflow 2: Schema Versioning with Git

**Goal:** Keep schema versions in git, apply reviewed versions locally

```bash
# Prepare schema file and commit to git
vim schemas/network-v7.yaml
git add schemas/network-v7.yaml
git commit -m "Update network schema to v7"

# On your dev machine, import from git-tracked schema
EDITOR=./snapcraft-import-editor \
  snapcraft edit-confdb-schema $ACCOUNT_ID network

# When prompted:
# Enter the path to the YAML file to import: /path/to/repo/schemas/network-v7.yaml

# Review the diff, confirm import

# Sign and install
./snapcraft-sign-and-ack -k my-key

# Test with observer snaps
```

**Why this works:**
- Team members review schema PRs before merge
- Git history tracks all schema versions
- Easy to revert: just re-import an older file from git
- Peer review before local testing

### Workflow 3: Testing Hook Behavior

**Goal:** Sign a schema without changing the revision (rare)

```bash
# You want to test the same revision multiple times
# (e.g., debugging why a change-view hook rejects a specific value)

./snapcraft-sign-and-ack -k my-key --no-bump schema.yaml

# The revision stays the same; observers don't see a "new" schema
# Useful for isolating hook behavior
```

## Troubleshooting

### Error: "File not found" when using snapcraft-hold-editor

**Problem:**
```
Error: File not found: ~/.snapcraft-hold/confdb-schema-edit.yaml
```

**Cause:** The first terminal (running `snapcraft edit-confdb-schema`) hasn't saved the hold file yet.

**Solution:** Make sure `snapcraft-hold-editor` is running as the `$EDITOR` before calling `snapcraft edit-confdb-schema`. The order matters:

```bash
# Correct: set EDITOR first, then call snapcraft
EDITOR=./snapcraft-hold-editor snapcraft edit-confdb-schema $ACCOUNT_ID $NAME

# Wrong: calling snapcraft without EDITOR set
snapcraft edit-confdb-schema $ACCOUNT_ID $NAME  # Uses default editor, no hold file
```

### Error: "snap keys" returns no keys

**Problem:**
```
./snapcraft-sign-and-ack -k my-key
Error: Failed to sign assertion
Tip: Make sure key 'my-key' exists (check with 'snap keys')
```

**Cause:** The signing key doesn't exist or has a different name.

**Solution:** List your available keys and use the correct name:

```bash
snap keys
# Output: Name    SHA3-384 fingerprint    ...
# my-key  abcd1234...

# Use the key name from the output
./snapcraft-sign-and-ack -k my-key schema.yaml
```

### Observers don't see the new schema after sign-and-ack

**Problem:** You signed and acknowledged a new schema, but observer snaps still read old values.

**Cause:** Observers cache the schema in memory; they don't automatically refresh.

**Solution:** Reconnect or restart observer snaps to force a reload:

```bash
# Option 1: Disconnect and reconnect
sudo snap disconnect my-observer-snap:my-app-state

sudo snap connect my-observer-snap:my-app-state

# Option 2: Restart the observer snap
sudo snap restart my-observer-snap

# Verify the new schema is loaded
snap known confdb-schema name=$SCHEMA_NAME | grep revision
```

## Integration with the ConfDB Skill

These scripts support the workflows described in the main skill documentation:

| Script | Used In Reference | Context |
|--------|-------------------|---------|
| `snapcraft-hold-editor` | [CONFDB_GETTING_STARTED.md](./CONFDB_GETTING_STARTED.md) | Alternative to manual `yaml-to-sign-json.py` workflow |
| `snapcraft-sign-and-ack` | [CONFDB_MIGRATION_GUIDE.md](./CONFDB_MIGRATION_GUIDE.md) | Step 2: Sign and Import Schema |
| `yaml-to-sign-json.py` | [CONFDB_GETTING_STARTED.md](./CONFDB_GETTING_STARTED.md) | Schema signing and import |

## Next Steps

- Read [CONFDB_GETTING_STARTED.md](./CONFDB_GETTING_STARTED.md) for manual signing workflows (if you prefer not to use scripts)
- Read [CONFDB_MIGRATION_GUIDE.md](./CONFDB_MIGRATION_GUIDE.md) for the complete migration playbook
- Read [CONFDB_HOOKS.md](./CONFDB_HOOKS.md) for custodian and observer hook patterns (needed after your schema is installed)
