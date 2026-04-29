# Confdb Schema Design

## Schema Structure

A confdb schema assertion defines:
- **storage** — the shape of the data stored internally
- **views** — named access paths that map request keys to storage keys, with access controls

**schema.yaml:**
```yaml
storage:
  schema:
    my-app:
      type: map
      schema:
        field-one:
          type: string
        field-two:
          type: int
        field-three:
          type: string

views:
  admin:
    rules:
      - request: my-app
        storage: my-app
        access: read-write

  state:
    rules:
      - request: my-app
        storage: my-app
        access: read
```

### Supported Field Types

These are the exact type names recognised by confdb (lowercase, as they appear in the schema):

| Type | Description | Constraints |
|------|-------------|-------------|
| `string` | UTF-8 string | `pattern` (regex), `choices` |
| `int` | 64-bit integer | `min`, `max`, `choices` |
| `number` | 64-bit float | `min`, `max`, `choices` |
| `bool` | Boolean | — |
| `map` | Key-value map | `schema` (per-key), `keys` (key type), `values` (value type), `required` |
| `array` | Ordered list | element type definition, `unique` |
| `any` | Accepts any value | — |

User-defined type aliases can be referenced as `${alias-name}`.

### Advanced Field Constraints

**Secret fields** — marked `visibility: secret`. Snapd will redact these values from responses unless the caller holds admin access:

```yaml
storage:
  schema:
    my-app:
      type: map
      schema:
        api-key:
          type: string
          visibility: secret
```

**Ephemeral fields** — marked `ephemeral: true`. Snapd does not persist these values; the custodian's `save-view` hook is responsible for storing them externally:

```yaml
storage:
  schema:
    my-app:
      type: map
      schema:
        session-token:
          type: string
          ephemeral: true
```

### Key Design Decisions

| Decision | Guidance |
|----------|----------|
| Field types | Use `string`, `int`, `bool` as appropriate — confdb validates against the schema |
| View access | Use `read-write` for custodian control views, `read` for observer state views |
| View granularity | Expose only what observers need — views can cover a subset of the storage tree |
| Computed values | Do **not** store computed/derived values in confdb; compute them at runtime in application code |

For naming rules (view names, plug names, storage paths), see [CONFDB_NAMING_CONVENTIONS.md](./CONFDB_NAMING_CONVENTIONS.md).

## Defaults File

The defaults file ships with your custodian snap and provides placeholder values. At configure time, placeholders are replaced with real values before writing to confdb.

**snap/local/configuration/defaults/config.yaml:**
```yaml
field-one: "field-one-placeholder"
field-two: 0
field-three: "field-three-placeholder"
```

Defaults files serve two purposes:
1. They define the expected shape of the configuration
2. They allow the configure hook to detect unset fields by checking for placeholder strings

The defaults file lives under `$SNAP/etc/configuration/defaults/` at runtime.

## Schema Evolution

Plan for schema changes from the start. Once a schema assertion is published and observers depend on it, changes to storage layout are breaking.

### Use a Version Prefix in Storage Paths

Prefix all storage keys with a version literal:

```yaml
# Good — can introduce v2 later without breaking v1 readers
views:
  admin:
    rules:
      - request: config
        storage: v1.my-app
        access: read-write
```

```yaml
# Risky — no room to evolve the storage layout
views:
  admin:
    rules:
      - request: config
        storage: my-app
        access: read-write
```

### Adding New Fields

New optional fields can be added to the schema without breaking existing observers. Required fields are harder — existing custodians must be updated to supply them before the schema is re-signed and imported.

### Renaming or Removing Fields

Introduce the new field under a new version prefix, migrate custodians and observers, then deprecate the old path. Never rename storage keys in place; observers depending on the old key will break silently.
