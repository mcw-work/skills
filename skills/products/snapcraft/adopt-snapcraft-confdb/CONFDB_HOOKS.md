# Confdb Hook Patterns

## Hook Types Reference

| Hook | When it runs | Can access confdb? | Purpose |
|------|-------------|-------------------|---------|
| `install` | Snap installation | ❌ No | Copy files to `$SNAP_COMMON` |
| `configure` | `snap set` command | ✅ Read-write | Validate snap config values and write to confdb |
| `connect-plug-X` | Interface connection | ❌ No | Log connection, restart services |
| `change-view-X` | Any snap writes to this view | ✅ Read-write (custodian only) | Validate, modify, or reject the write before commit |
| `observe-view-X` | A write to this view is committed | ✅ Read-only | React to data changes (non-custodians; errors ignored by snapd) |
| `save-view-X` | After `change-view` completes | ✅ Read-only | Persist ephemeral data to an external store |
| `load-view-X` | Before data is read into a transaction | ✅ Read-write (custodian only) | Inject or transform data from an external store |
| `query-view-X` | On a parameterised query | ✅ Read-write (custodian only) | Filter or compute query results |

All five confdb-specific hook names match `<hook-type>-view-<plug-name>`, where `<plug-name>` is the snap's plug name from `snapcraft.yaml`.

## ⚠️ Critical Rules

1. **Never access confdb in connect hooks** — this causes a deadlock because snapd holds the interface lock during connect hook execution
2. **A `role: custodian` plug must be connected** — any write to confdb requires at least one snap with `role: custodian` connected to that view; writes fail with `"cannot commit changes to confdb: no custodian snap connected"` otherwise
3. **`change-view` is for custodians validating writes, not for observers** — use `observe-view` to react to data changes in non-custodian snaps
4. **Validate completeness before writing** — never write partial configuration to confdb
5. **Always exit successfully from hooks** — log errors instead of failing; a failing hook blocks snap operations

---

## Custodian Configure Hook

The configure hook is the primary write path. It runs whenever `snap set` is called on the custodian.

**snap/hooks/configure:**
```python
#!/usr/bin/env python3

import os
import subprocess
import sys
import logging
import logging.handlers

logger = logging.getLogger("configure-hook")
logger.setLevel(logging.INFO)
try:
    syslog = logging.handlers.SysLogHandler(address='/dev/log')
    syslog.setFormatter(logging.Formatter('my-snap.configure: %(message)s'))
    logger.addHandler(syslog)
except Exception:
    pass

DEFAULTS_FILE = os.path.join(
    os.environ.get("SNAP", ""),
    "etc/configuration/defaults/config.yaml"
)

def get_snap_config(key):
    result = subprocess.run(
        ["snapctl", "get", key],
        capture_output=True, text=True, check=False
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None

try:
    if not os.path.exists(DEFAULTS_FILE):
        logger.error(f"Defaults file not found: {DEFAULTS_FILE}")
        sys.exit(0)

    field_one = get_snap_config("field-one")
    field_two = get_snap_config("field-two")
    field_three = get_snap_config("field-three")

    # Validate all required values are present
    missing = [k for k, v in {"field-one": field_one, "field-two": field_two, "field-three": field_three}.items() if not v]
    if missing:
        logger.info(f"Configuration incomplete, missing: {', '.join(missing)}. Skipping confdb update.")
        sys.exit(0)

    logger.info("All configuration values present, updating confdb")

    with open(DEFAULTS_FILE, 'r') as f:
        config_data = f.read()

    config_data = config_data.replace("field-one-placeholder", field_one)
    config_data = config_data.replace("field-three-placeholder", field_three)

    result = subprocess.run(
        ["snapctl", "set", ":my-app-admin", "--view", f"my-app={config_data}"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        logger.warning(f"Failed to write to confdb: {result.stderr}")
    else:
        logger.info("Configuration written to confdb")

except Exception as e:
    logger.error(f"Error in configure hook: {e}")

sys.exit(0)
```

**Pattern summary:**
1. Read all required values from `snapctl get`
2. Check that ALL values are present — list the missing ones for observability
3. If any are missing, log and exit successfully (do not write partial config)
4. Replace placeholders in the defaults file
5. Write the complete config to confdb via `snapctl set :plug-name --view`

---

## ❌ Pitfall: Writing Partial Configuration

```python
# Wrong — ships broken config if any value is None
field_one = get_snap_config("field-one")
subprocess.run(["snapctl", "set", ":my-app-admin", "--view", f"field-one={field_one}"])
```

```python
# Correct — validate completeness first, then write atomically
missing = [k for k, v in fields.items() if not v]
if missing:
    logger.info(f"Incomplete config, skipping: {missing}")
    sys.exit(0)
# only reach here if all values are set
```

---

## Observer Connect Hook

The connect hook fires when an observer's interface is connected. It must **not** access confdb.

**snap/hooks/connect-plug-my-app-state:**
```bash
#!/bin/sh -e

logger -t "my-app-snap.connect-plug" "Config interface connected"

# Restart service so it picks up the latest confdb values on next read
if snapctl services my-app-snap.service | grep -q active; then
    snapctl restart my-app-snap.service
fi

exit 0
```

## ❌ Pitfall: Accessing Confdb in a Connect Hook

```bash
# Wrong — causes deadlock
snapctl set :my-app-admin --view key=value
```

```bash
# Correct — only log and restart; let configure/change-view hooks handle confdb
logger -t my-snap "Interface connected"
```

---

## Reading Configuration in an Observer

Use this utility in your observer's application code or `observe-view` hook:

**confdb_utils.py:**
```python
import subprocess
import yaml
import logging

logger = logging.getLogger(__name__)

def get_config_from_confdb(view=":my-app-state"):
    """Read all configuration from a confdb view."""
    try:
        result = subprocess.run(
            ["snapctl", "get", view, "--view", "my-app"],
            capture_output=True, text=True, check=True
        )
        config_data = result.stdout.strip()
        if not config_data:
            logger.warning("No configuration data found in confdb")
            return None

        config = yaml.safe_load(config_data)

        # Detect uninitialized placeholders
        for key, value in config.items():
            if isinstance(value, str) and "placeholder" in value.lower():
                logger.warning(f"Configuration not ready, placeholder found: {key}={value}")
                return None

        return config

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to read from confdb: {e}")
        return None
    except Exception as e:
        logger.error(f"Error parsing confdb config: {e}")
        return None


def get_config_value(key, view=":my-app-state"):
    """Get a single configuration value from a confdb view."""
    try:
        result = subprocess.run(
            ["snapctl", "get", view, "--view", key],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip() or None
    except subprocess.CalledProcessError:
        return None
```

## ❌ Pitfall: Not Checking for Placeholders

```python
# Wrong — config may contain "server-url-placeholder" if not yet configured
config = get_config_from_confdb()
url = config["server-url"]
requests.get(url)  # fails with an invalid URL
```

```python
# Correct — get_config_from_confdb() returns None if placeholders are present
config = get_config_from_confdb()
if config is None:
    return  # not yet configured; try again later
```

---

## Observer: observe-view Hook

The `observe-view-<plug-name>` hook fires after a write to the view is committed, for every connected snap that is **not** the snap that made the write. This is how observers react to live configuration changes.

> Hook errors are **ignored by snapd** — a failing `observe-view` hook does not block the transaction.

**snap/hooks/observe-view-my-app-state:**
```bash
#!/bin/sh -e

logger -t "my-app-snap.observe-view" "Config changed, reloading service"

# Read updated values before restarting
NEW_VALUE=$(snapctl get :my-app-state --view my-app.field-one 2>/dev/null || echo "")
logger -t "my-app-snap.observe-view" "New field-one: $NEW_VALUE"

if snapctl services my-app-snap.service | grep -q active; then
    snapctl restart my-app-snap.service
fi
```

**snapcraft.yaml:**
```yaml
hooks:
  observe-view-my-app-state:
    plugs: [my-app-state]
```

Rules for `observe-view` hooks:
- `snapctl get :plug-name --view` — ✅ allowed
- `snapctl get :plug-name --view --previous` — ✅ allowed (reads values before the write)
- `snapctl set :plug-name --view` — ❌ not allowed (read-only hook)

---

## Custodian: change-view Hook

The `change-view-<plug-name>` hook runs on the custodian snap **before** a transaction is committed. The custodian can read and modify the incoming values, or abort the transaction entirely.

**snap/hooks/change-view-my-app-admin:**
```python
#!/usr/bin/env python3
import subprocess, sys, logging, logging.handlers

logger = logging.getLogger("change-view")
try:
    h = logging.handlers.SysLogHandler(address='/dev/log')
    h.setFormatter(logging.Formatter('my-snap.change-view: %(message)s'))
    logger.addHandler(h)
except Exception:
    pass

try:
    # Read the incoming value
    result = subprocess.run(
        ["snapctl", "get", ":my-app-admin", "--view", "my-app.field-two"],
        capture_output=True, text=True, check=True
    )
    value = result.stdout.strip()

    # Validate
    if value and not value.isdigit():
        logger.error(f"field-two must be an integer, got: {value}")
        sys.exit(1)  # non-zero exit aborts the transaction

    logger.info(f"Validated field-two={value}")

except Exception as e:
    logger.error(f"Error in change-view hook: {e}")
    sys.exit(1)

sys.exit(0)
```

---

## Custodian: save-view Hook

The `save-view-<plug-name>` hook runs after all `change-view` hooks complete. It is used by custodians to persist **ephemeral** data (fields marked `ephemeral: true` in the schema) to an external store, since snapd does not persist ephemeral values itself.

**snap/hooks/save-view-my-app-admin:**
```bash
#!/bin/sh -e

# Read ephemeral fields that need external persistence
TOKEN=$(snapctl get :my-app-admin --view my-app.session-token 2>/dev/null || echo "")

if [ -n "$TOKEN" ]; then
    # Write to external store (e.g. a keyring, file, or API)
    echo "$TOKEN" > "$SNAP_COMMON/session-token"
    logger -t my-snap "Persisted session token"
fi
```

`save-view` hooks may only call `snapctl get :plug --view` — `snapctl set` is not permitted here.

---

## Updating File-Based Config (Content Slot Compatibility)

If your custodian also exposes a content slot for snaps that cannot use confdb, the configure hook must update both confdb **and** the content-slot files atomically.

**snap/local/update-config-files.sh:**
```bash
#!/bin/sh -e

CONFIG_DIR="$SNAP_COMMON/configuration"

if [ ! -d "$CONFIG_DIR" ]; then
    logger -t my-snap "ERROR: Configuration directory not found"
    exit 1
fi

replace_in_files() {
    local placeholder="$1"
    local value="$2"
    [ -z "$value" ] && return
    find "$CONFIG_DIR" -type f -exec sed -i "s#${placeholder}#${value}#g" {} \;
}

FIELD_ONE=$(snapctl get field-one 2>/dev/null || echo "")
FIELD_THREE=$(snapctl get field-three 2>/dev/null || echo "")

replace_in_files "field-one-placeholder" "$FIELD_ONE"
replace_in_files "field-three-placeholder" "$FIELD_THREE"

logger -t my-snap "Configuration files updated"
```

Call this script from the configure hook **after** writing to confdb:

```python
# Update confdb first
subprocess.run(["snapctl", "set", ":my-app-admin", "--view", ...], check=True)

# Then sync files for content-slot consumers
subprocess.run([f"{os.environ['SNAP']}/usr/bin/update-config-files.sh"], check=True)
```

## ❌ Pitfall: Forgetting to Sync Content Slot Files

```python
# Wrong — confdb updated but content slot consumers see stale data
subprocess.run(["snapctl", "set", ":my-app-admin", "--view", f"my-app={config}"])
# Missing: update files for content slot
```

---

## Additional snapctl Commands

```bash
# Unset a field in confdb (custodian only, change-view context)
snapctl unset :my-app-admin --view my-app.field-one

# Read the value of a field before the current transaction (change-view, save-view, observe-view only)
snapctl get :my-app-admin --view --previous my-app.field-one
```

---

## Logging in Hooks

Use the system journal — never write to files in hooks.

```python
# Wrong — file logging in hooks
with open(f"{os.environ['SNAP_COMMON']}/hooks.log", "a") as f:
    f.write("Hook ran\n")
```

```python
# Correct — syslog/journalctl
import logging, logging.handlers
logger = logging.getLogger("my-snap")
try:
    h = logging.handlers.SysLogHandler(address='/dev/log')
    h.setFormatter(logging.Formatter('my-snap: %(message)s'))
    logger.addHandler(h)
except Exception:
    pass
logger.info("Hook ran successfully")
```

Retrieve hook logs with:
```bash
sudo journalctl -u snapd | grep "my-snap"
```
