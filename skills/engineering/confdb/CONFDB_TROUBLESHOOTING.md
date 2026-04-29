# Troubleshooting Confdb

## Check Confdb Status

```bash
# View the imported confdb-schema assertion
snap known confdb-schema

# Read current confdb values from the custodian (control view)
sudo snap run my-config-snap.snapctl-wrapper get --view :my-app-admin -d | jq

# Read current confdb values from an observer (state view)
sudo snap run my-app-snap.snapctl-wrapper get --view :my-app-state -d | jq
```

## Check Hook Execution

```bash
# All hook activity for a snap
sudo journalctl -u snapd | grep "my-snap"

# Configure hook specifically
sudo journalctl -u snapd | grep "my-snap.configure"
```

## Check Interface Connections

```bash
# All connections for a snap
snap connections my-snap

# Confdb connections only
snap connections my-snap | grep confdb
```

---

## Diagnosing Connection Failures

If an observer cannot connect, work through these checks in order:

**1. Confirm the custodian is installed:**
```bash
snap list | grep my-config-snap
```

**2. Confirm the custodian has connected both plugs** — the observe plug must be connected before observers can join:
```bash
snap connections my-config-snap | grep -E "admin|state"
# Both should show "connected"
```

**3. Confirm confdb has been initialised** — the custodian must have written at least once:
```bash
sudo snap run my-config-snap.snapctl-wrapper get --view :my-app-admin -d
# Should return config data, not empty or an error
```

**4. Confirm the observer snap declares the plug correctly:**
```bash
snap info my-app-snap | grep plugs
```

---

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `cannot commit changes to confdb: no custodian snap connected` | No snap with `role: custodian` is connected to this view | Install and connect the custodian snap; ensure its plug declares `role: custodian` |
| `view not found` | Typo in view name, or schema not imported | Verify view name matches the schema assertion; run `snap known confdb-schema` |
| `permission denied` | Snap trying to write to a read-only view | Use the admin/read-write view for writes; only assign `access: read` to observer views |
| `deadlock detected` | Confdb accessed inside a connect hook | Move all confdb reads and writes to `configure`, `change-view`, or `observe-view` hooks |

---

## No Custodian Snap Connected

**Symptom:** writing to confdb fails with `"cannot commit changes to confdb: no custodian snap connected"`.

**Cause:** No snap with `role: custodian` on its plug is currently connected to the view being written.

**Fix:**
1. Verify the custodian snap declares `role: custodian` on the relevant plug:
   ```bash
   snap info my-config-snap | grep -A5 "plugs:"
   ```
2. Verify the plug is connected:
   ```bash
   snap connections my-config-snap | grep confdb
   ```
3. If not connected, connect it:
   ```bash
   sudo snap connect my-config-snap:my-app-admin
   ```
4. Run the configure hook again to trigger the write:
   ```bash
   sudo snap set my-config-snap field-one=value
   ```

---

## Best Practices Summary

✅ **Do:**
- Validate ALL required config values before writing to confdb
- Use `journalctl` logging (via `logger` or `SysLogHandler`) instead of file logging
- Exit successfully from all hooks; log errors rather than failing
- Gate integration tests behind an environment variable
- Use `mock_open` without `read_data` in unit tests; patch `yaml.safe_load` separately
- Keep content-slot files in sync if maintaining backward compatibility
- Connect custodian plugs (with `role: custodian`) before attempting any writes
- Use `observe-view-<plug>` hooks in observer snaps to react to live config changes
- Use version prefixes (`v1.`) in storage paths to allow future schema evolution

❌ **Don't:**
- Forget to declare `role: custodian` on the custodian's plug
- Access confdb in connect hooks (causes deadlock)
- Write partial configuration to confdb (validate completeness first)
- Hardcode config values — read from defaults files and replace placeholders
- Use file-based logging in hooks
- Run integration tests in the normal unit test suite without the environment gate
- Forget to connect the custodian's observe plug before observers
- Store computed/derived values in confdb — compute them at runtime instead
