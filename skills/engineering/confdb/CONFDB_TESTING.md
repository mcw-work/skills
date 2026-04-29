# Testing Confdb Snaps

## Unit Tests

Unit tests mock filesystem and subprocess calls to test hook logic in isolation.

**pytest.ini:**
```ini
[pytest]
markers =
    unit: Unit tests that do not require external dependencies
    integration: Integration tests that require a running snap environment
```

### Mocking File I/O

```python
from unittest.mock import patch, mock_open
import pytest

@pytest.mark.unit
@patch("pathlib.Path.is_file", return_value=True)
@patch("builtins.open", new_callable=mock_open)
def test_read_config(mock_file, mock_is_file):
    with patch("yaml.safe_load", return_value={"field-one": "value"}):
        result = read_config_file("test.yaml")
        assert result["field-one"] == "value"
```

> **Note:** Use `mock_open` without `read_data` when you need `yaml.safe_load` to see patched return values — patch `yaml.safe_load` separately.

### Mocking snapctl

```python
from unittest.mock import patch, MagicMock
import subprocess

@pytest.mark.unit
def test_configure_hook_writes_to_confdb():
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "value\n"

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        run_configure_hook()
        calls = [str(c) for c in mock_run.call_args_list]
        assert any("snapctl" in c and "set" in c and "--view" in c for c in calls)
```

### Mocking Placeholder Detection

```python
@pytest.mark.unit
def test_get_config_returns_none_on_placeholder():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "field-one: field-one-placeholder\n"
        result = get_config_from_confdb()
        assert result is None
```

---

## Integration Tests

Integration tests require a real snap installation with confdb enabled. Gate them with an environment variable so they never run in CI without explicit opt-in.

```python
import os
import pytest

@pytest.mark.integration
def test_confdb_round_trip():
    if not os.environ.get("RUN_INTEGRATION_TESTS"):
        pytest.skip("Set RUN_INTEGRATION_TESTS=1 to run integration tests")

    # Set a value via the custodian
    set_confdb_value("my-config-snap", ":my-app-admin", "my-app.field-one", "test-value")

    # Read it back via the observer view
    values = get_confdb_values("my-config-snap", ":my-app-state")
    assert values["my-app"]["field-one"] == "test-value"
```

## snapctl Wrapper for Integration Tests

`snapctl` can only be called from within a snap context, so expose a thin wrapper app in your custodian to allow test code to invoke it:

**snapcraft.yaml:**
```yaml
apps:
  snapctl-wrapper:
    command: snap/local/snapctl-wrapper.sh
    plugs: [my-app-admin]  # Must include the confdb plug
```

**snap/local/snapctl-wrapper.sh:**
```bash
#!/bin/sh
exec snapctl "$@"
```

**Test helpers:**
```python
import subprocess
import json

def set_confdb_value(snap_name, view, key, value):
    subprocess.run([
        "snap", "run", f"{snap_name}.snapctl-wrapper",
        "set", "--view", view, f"{key}={value}"
    ], check=True)

def get_confdb_values(snap_name, view):
    result = subprocess.run([
        "snap", "run", f"{snap_name}.snapctl-wrapper",
        "get", "--view", view, "-d"
    ], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)
```

> **Important:** The `snapctl-wrapper` app must declare the confdb plug it is exercising. Without the plug, `snapctl` will reject the call.
