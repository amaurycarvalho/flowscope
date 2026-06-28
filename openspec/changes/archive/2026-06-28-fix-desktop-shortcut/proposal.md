## Why

The `--create-shortcut` flag creates a `.desktop` file with a relative `Exec` path and an `Icon` path that resolves to a PyInstaller temp directory (`/tmp/...`), making the shortcut non-functional after the application exits. Additionally, GUI users on Linux have no way to create the shortcut from within the application.

## What Changes

- `--create-shortcut` now resolves `Exec` to an absolute path and copies the icon to `~/.local/share/icons/` (a permanent XDG-compliant location)
- `.desktop` file now includes `StartupNotify=true` and `--gui` flag in Exec
- A dynamic "Criar atalho no desktop" button appears in the GUI top bar on Linux when no shortcut exists, and hides immediately after successful creation
- Shared utility function for icon resolution handling both dev (`__file__`) and frozen (`sys._MEIPASS`) modes

## Capabilities

### New Capabilities
- `gui-shortcut-button`: Button in the GUI top bar on Linux that creates a desktop shortcut, visible only when none exists, with status bar feedback

### Modified Capabilities
- `desktop-shortcut`: Expand requirements to cover correct Exec path resolution (absolute), Icon path (copied to `~/.local/share/icons/`), and `StartupNotify=true`

## Impact

- `src/flowscope/presentation/main.py` - `_create_desktop_shortcut()` logic
- `src/flowscope/presentation/gui/app.py` - new button in `_build_top_bar()`, shortcut existence check
- `src/flowscope/presentation/cli.py` - no change (argument already defined)
- Tests in `tests/test_presentation/test_main.py` and new tests for GUI button
