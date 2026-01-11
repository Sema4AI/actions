# Action Server Developer Toolkit

Build action-server binary using RCC for isolated, reproducible builds.

**Prerequisite:** RCC installed and available in PATH.

## Usage

Run from the `actions/` repository root:

```bash
# Build community tier (frontend + PyInstaller + Go wrapper)
rcc run -r action_server/developer/toolkit.yaml -t community

# Build enterprise tier (requires NPM_TOKEN)
rcc run -r action_server/developer/toolkit.yaml -t enterprise
```

## Output

The final binary is created at:
```
action_server/dist/final/action-server
```

Test with:
```bash
./action_server/dist/final/action-server version
```

## Dependencies

Defined in `setup.yaml` - RCC automatically creates the environment with:
- Python 3.12, Node.js 20, Go, uv, invoke, poetry, ruff, pytest, mypy, pyinstaller
- Local packages: build_common, devutils, common, action_server
