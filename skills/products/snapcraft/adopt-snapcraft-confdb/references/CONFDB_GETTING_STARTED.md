# Getting Started with Confdb

## Enable the Confdb Feature

Confdb is currently an experimental feature. Enable it on your development system:

```bash
sudo snap set system experimental.confdb=true
```

## Create a Signing Key

All confdb-schema assertions must be signed with a key registered to your Snap Store account.

```bash
# Generate a new key
snap create-key my-confdb-key

# Register the key with your store account (requires snapcraft)
snapcraft register-key my-confdb-key

# List your keys
snap keys
```

## Sign and Import a Schema

Once you have a schema YAML file (see [CONFDB_SCHEMA_DESIGN.md](./CONFDB_SCHEMA_DESIGN.md)), convert, sign, and import it:

```bash
#!/bin/sh -e
# sign-schema.sh <schema.yaml> <key-name>
SCHEMA_FILE=$1
KEY_NAME=$2

# Convert YAML to the JSON format expected by snap sign
./yaml-to-sign-json.py "$SCHEMA_FILE" > schema.json

# Sign the schema assertion
snap sign -k "$KEY_NAME" < schema.json > schema.assert

# Import the signed assertion into snapd
sudo snap ack schema.assert

# Verify
echo "Imported schema revision:"
snap known confdb-schema | grep revision | head -1
```

> **Note:** You will need a helper script (`yaml-to-sign-json.py`) to convert your YAML schema into the JSON assertion format that `snap sign` expects. The exact format depends on the assertion fields required by snapd — refer to the [confdb documentation](https://snapcraft.io/docs/confdb) for the current assertion schema.

## Verify Your Setup

```bash
# Confirm the feature is enabled
snap get system experimental.confdb

# Confirm your schema is loaded
snap known confdb-schema

# Confirm your key is available
snap keys
```
