# Confdb Schema Editing Toolkit — Developer Guide

A collection of helper utilities for developers to edit, sign, and manage confdb schemas **locally** during development **without** uploading to the Snap Store.

## Overview

When developing confdb schemas, snapcraft's built-in `edit-confdb-schema` command immediately uploads any changes to the Snap Store. This toolkit provides manual helper scripts that work around that limitation, allowing you to:

- **Export** confdb schemas to persistent local files for external editing (not just snapcraft's temp editor)
- **Import** existing schema files from your version control or other sources
- **Automatically sign and acknowledge** modified schemas using local snapd keys (no store interaction)
- **Convert** YAML schemas to JSON format for `snap sign` without manual steps

**Key Principle:** These scripts keep your schema **local** until you're ready to publish to the store.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Scripts](#scripts)
  - [snapcraft-hold-editor](#snapcraft-hold-editor)
  - [snapcraft-import-editor](#snapcraft-import-editor)
  - [snapcraft-sign-and-ack](#snapcraft-sign-and-ack)
  - [yaml-to-sign-json.py](#yaml-to-sign-jsonpy)
- [Workflows](#workflows)
  - [Quick Edit and Sign](#quick-edit-and-sign)
  - [Export, Edit, and Manual Sign](#export-edit-and-manual-sign)
  - [Import Existing Schema](#import-existing-schema)
- [Environment Variables](#environment-variables)
- [Examples](#examples)

## Prerequisites

- `snapcraft` installed and authenticated (`snapcraft login`)
- `snap sign` available with signing keys configured (`snap keys`)
- Python 3 with `yaml` module for conversion scripts
- Bash shell

## Scripts

### snapcraft-hold-editor

**Purpose:** Intercepts snapcraft's temporary file, saves it persistently, and waits for external editing.

**Usage:**
```bash
EDITOR=/path/to/snapcraft-hold-editor snapcraft edit-confdb-schema <account-id> <name>
```

**Features:**
- Saves schema to `~/.snapcraft-hold/confdb-schema-edit.yaml`
- Creates timestamped backups
- Displays helpful instructions with commands
- Optionally launches real editor via `$REAL_EDITOR`
- Waits for user confirmation before returning to snapcraft

**Environment Variables:**
- `SNAPCRAFT_HOLD_DIR` - Override hold directory location (default: `~/.snapcraft-hold`)
- `REAL_EDITOR` - Editor to launch automatically (e.g., `vim`, `code`, `subl`)

**Example:**
```bash
# Basic usage - manual editing in another terminal
EDITOR=~/canonical/confdb-demo-editing/snapcraft-hold-editor \
  snapcraft edit-confdb-schema VX84EGFo6txXHSNk4l55reEiaU5n7I7R network

# With automatic editor launch
EDITOR=~/canonical/confdb-demo-editing/snapcraft-hold-editor \
  REAL_EDITOR=vim \
  snapcraft edit-confdb-schema VX84EGFo6txXHSNk4l55reEiaU5n7I7R network
```

### snapcraft-import-editor

**Purpose:** Imports an existing YAML file as the confdb schema for snapcraft.

**Usage:**
```bash
EDITOR=/path/to/snapcraft-import-editor snapcraft edit-confdb-schema <account-id> <name>
```

**Features:**
- Prompts for file path to import
- Supports `~` expansion and relative paths
- Shows unified diff between current and import file in `less`
- Displays metadata comparison (account-id, name, revision)
- Requires confirmation before importing

**Example:**
```bash
EDITOR=~/canonical/confdb-demo-editing/snapcraft-import-editor \
  snapcraft edit-confdb-schema VX84EGFo6txXHSNk4l55reEiaU5n7I7R network

# Then enter path when prompted:
# Enter the path to the YAML file to import: ~/my-schemas/network-v7.yaml
```

### snapcraft-sign-and-ack

**Purpose:** Automates the complete workflow of converting, signing, and acknowledging a confdb schema locally (no Snap Store interaction). This is the final step after editing your schema with `snapcraft-hold-editor` or `snapcraft-import-editor`.

**Usage:**
```bash
./snapcraft-sign-and-ack [OPTIONS] [YAML_FILE]
```

**Options:**
- `-k, --key-name NAME` - Name of the signing key (required)
- `--no-bump` - Don't auto-bump revision number
- `--dry-run` - Show commands without executing
- `-h, --help` - Show help message

**Workflow Steps:**
1. Converts YAML to JSON using `yaml-to-sign-json.py`
2. Signs the JSON assertion with your local key using `snap sign`
3. Acknowledges the signed assertion into snapd using `snap ack`

**Revision Bumping Guidance:**

By default, `snapcraft-sign-and-ack` auto-bumps the revision number (e.g., 5 → 6). This is the **recommended behavior** for local development because:

- ✅ **Each sign-and-ack bumps the schema** — observers will see the new version
- ✅ **Prevents "already exists" conflicts** — same revision twice is a local error
- ✅ **Tracks development progress** — revision history shows iteration count

**Use `--no-bump` only when:**
- Testing the same revision locally (e.g., debugging hook behavior without schema changes)
- Importing a pre-signed schema file and don't want to alter the revision
- Manually managing revision numbers (rare)

**Examples:**
```bash
# Default workflow: hold-edit-sign cycle with auto-bump
EDITOR=./snapcraft-hold-editor snapcraft edit-confdb-schema $ACCOUNT $NAME
# (edit file in another terminal, then press Enter)
./snapcraft-sign-and-ack -k default
# Revision is now automatically bumped, snapd has the new schema

# Specify a custom YAML file (e.g., from version control)
./snapcraft-sign-and-ack -k mykey ~/projects/schemas/network-v7.yaml

# Testing without revision changes (rare)
./snapcraft-sign-and-ack -k mykey --no-bump schema.yaml

# Preview what will happen without executing
./snapcraft-sign-and-ack -k mykey --dry-run schema.yaml
```

**Default File Location:**
If no YAML file is specified, uses `~/.snapcraft-hold/confdb-schema-edit.yaml` (the default output from `snapcraft-hold-editor`). This makes it seamless in the quick edit-and-sign workflow:
```bash
EDITOR=./snapcraft-hold-editor snapcraft edit-confdb-schema $ACCOUNT $NAME
./snapcraft-sign-and-ack -k mykey  # automatically finds the hold file
```

### yaml-to-sign-json.py

**Purpose:** Converts a YAML confdb schema to JSON format required by `snap sign`. This is used internally by `snapcraft-sign-and-ack` but can also be run directly for manual signing workflows.

**Usage:**
```bash
./yaml-to-sign-json.py <input.yaml>
# Output goes to stdout; redirect or pipe as needed
```

**What It Does:**
- Auto-adds `type: confdb-schema` if missing
- Auto-adds `authority-id` from `account-id` if not already present
- Auto-generates RFC3339 `timestamp` if missing
- Ensures `revision` is a string (as required by snap sign)
- Handles `body` field correctly (keeps as JSON string, not object)
- Removes fields like `body-length` and `sign-key-sha3-384` (snap sign will add these)

**When to Use Directly:**
- You want manual control over each signing step (advanced)
- Integrating confdb signing into custom scripts
- Debugging the conversion process

**Examples:**
```bash
# Output to stdout (for inspection)
./yaml-to-sign-json.py schema.yaml

# Output to file
./yaml-to-sign-json.py schema.yaml > schema.json

# Pipe directly to snap sign (manual workflow)
./yaml-to-sign-json.py schema.yaml | snap sign -k mykey > schema.assert

# Then manually ack the result
snap ack schema.assert
```

**Note:** Most developers should use `snapcraft-sign-and-ack` instead, which calls this script automatically.

## Workflows

### Quick Edit and Sign (Recommended for Development)

**Best for:** Rapid iteration during development. Least friction, most common workflow.

**Steps:**
```bash
# 1. Start the hold-editor with snapcraft
#    (This will wait for you to edit and press Enter)
EDITOR=./snapcraft-hold-editor \
  snapcraft edit-confdb-schema VX84EGFo6txXHSNk4l55reEiaU5n7I7R network

# 2. In another terminal, edit the saved file
vim ~/.snapcraft-hold/confdb-schema-edit.yaml

# 3. Back in the first terminal, press Enter when done editing
#    (snapcraft will try to upload, but you'll abort next)

# 4. Abort the snapcraft upload with Ctrl+C
#    (We'll use snapcraft-sign-and-ack instead)

# 5. In the second terminal, sign and acknowledge locally
./snapcraft-sign-and-ack -k default

# 6. Verify the schema is loaded in snapd
snap known confdb-schema name=network | head -5
```

**Why This Workflow:**
- Schema stays on your local machine until you're ready to publish to the store
- Automatic revision bumping with each sign-and-ack prevents conflicts
- Fast iteration: edit → sign → test observers, repeat
- No store authentication required

### Import Existing Schema

**Best for:** Using schema files from git, applying reviewed changes, or pre-prepared versions.

**Steps:**
```bash
# 1. Prepare your YAML file (from git, a peer, etc.)
#    Ensure it has account-id, name, and revision fields
vim ~/my-schemas/network-v7.yaml

# 2. Import the file via snapcraft
EDITOR=./snapcraft-import-editor \
  snapcraft edit-confdb-schema VX84EGFo6txXHSNk4l55reEiaU5n7I7R network

# 3. When prompted, enter the path to your file
# Enter the path to the YAML file to import: ~/my-schemas/network-v7.yaml

# 4. Review the diff in less (press 'q' to exit)

# 5. Confirm import (y/N)

# 6. Abort the snapcraft upload with Ctrl+C

# 7. Sign and acknowledge locally
./snapcraft-sign-and-ack -k default
```

**Why This Workflow:**
- Centralizes schema versions in version control
- Peer-reviewed schemas before they hit local snapd
- Easy rollback: just re-import an older YAML file

### Manual Workflow (Advanced)

**Best for:** Custom scripts, CI/CD integration, or when you need precise control.

**Steps:**
```bash
# 1. Convert YAML to JSON manually
./yaml-to-sign-json.py schema.yaml > schema.json

# 2. Inspect the JSON if needed
cat schema.json

# 3. Sign with your key
cat schema.json | snap sign -k default > schema.assert

# 4. Acknowledge into snapd
snap ack schema.assert

# 5. Verify
snap known confdb-schema name=network | head -5
```

**Why This Workflow:**
- Full control over each step
- Useful for debugging conversion or signing issues
- Foundation for custom automation

## Environment Variables

### EDITOR
Specifies which "editor" snapcraft should use. Set this to one of the toolkit scripts.

**Example:**
```bash
EDITOR=~/canonical/confdb-demo-editing/snapcraft-hold-editor
```

### REAL_EDITOR
Used by `snapcraft-hold-editor` to launch your actual editor automatically.

**Example:**
```bash
REAL_EDITOR=vim
REAL_EDITOR=code
REAL_EDITOR=subl
```

### SNAPCRAFT_HOLD_DIR
Override the default directory where `snapcraft-hold-editor` saves files.

**Default:** `~/.snapcraft-hold`

**Example:**
```bash
SNAPCRAFT_HOLD_DIR=~/projects/confdb-schemas
```

