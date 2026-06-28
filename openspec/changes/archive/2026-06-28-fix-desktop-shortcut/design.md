## Context

The `_create_desktop_shortcut()` function in `main.py` uses `sys.argv[0]` for `Exec` (often relative) and resolves the icon path via `Path(__file__).resolve().parent.parent / "icons"` — which works in development but points to a wrong path in PyInstaller frozen builds (icons are at `sys._MEIPASS/icons/`, not `sys._MEIPASS/flowscope/icons/`). The existing `desktop-shortcut` spec only covers the Linux-only restriction, not path correctness.

The GUI (`app.py`) already resolves its icon correctly via a 3-level `.parent.parent.parent`, but duplicates the resolution logic.

## Goals / Non-Goals

**Goals:**
- `--create-shortcut` produces a .desktop file with absolute Exec path, `--gui` flag, permanent icon in `~/.local/share/icons/`, and `StartupNotify=true`
- GUI shows a "Criar atalho no desktop" button on Linux when no shortcut exists, hides it on success
- One shared icon-resolution utility for both CLI and GUI

**Non-Goals:**
- No system-wide installation (`/usr/share/applications/`)
- No shortcut deletion/uninstall feature
- No shortcut for Windows or macOS
- No changes to the PyInstaller packaging spec

## Decisions

### Decision 1: Shared icon resolution helper

Create `_resolve_icon_path()` in `main.py` or a new utility module that handles both dev and frozen modes:

```python
def _resolve_icon_path() -> Path:
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS) / "icons" / "flowscope.png"
    return Path(__file__).resolve().parent.parent / "icons" / "flowscope.png"
```

**Alternatives considered:**
- Using `pkg_resources` or `importlib.resources` — heavier for a single-file lookup
- Keeping duplicated logic in both `main.py` and `app.py` — violates DRY

### Decision 2: Icon installed to `~/.local/share/icons/`

The .desktop file references `~/.local/share/icons/flowscope.png` — a standard XDG data directory. The function copies the resolved icon there with `mkdir -p` before writing the .desktop file.

**Rationale:** PyInstaller's temp dir is ephemeral; referencing it would break on next app launch. `~/.local/share/icons/` is the standard user-level icon directory on Linux.

### Decision 3: GUI shortcut button logic

The button is added in `_build_top_bar()` conditionally:
- Check `platform.system() == "Linux"`
- Check `~/Desktop/flowscope.desktop` and `~/Área de Trabalho/flowscope.desktop` existence
- If missing, pack the button after "Copiar Dados"
- On click: call the same `_create_desktop_shortcut()` logic, catch `SystemExit`, call `_flash_status("Atalho criado!")`, and `btn.pack_forget()`
- On failure: `_set_status()` with error message, button remains visible

```python
# Flow in _build_top_bar():
[DateEntry] [Hoje] [Carregar] [Copiar Dados] [★ Atalho]  (label)
                                               ↑ new, conditional
```

**Alternatives considered:**
- Separate thread for creation — unnecessary, operation is < 50ms
- Confirmation dialog — user preferred no confirmation

### Decision 4: `_create_desktop_shortcut()` returns bool instead of calling `sys.exit()`

Currently the function calls `sys.exit(0)` on non-Linux and `sys.exit(1)` on error. To reuse it from the GUI (which shouldn't exit), the function will return a `bool` (success/failure) and raise `SystemExit` only from the CLI entry point.

## Risks / Trade-offs

- **[Path drift]** If the user moves the compiled binary after creating the shortcut, the `Exec` path becomes stale. Mitigation: document that the shortcut should be recreated after moving. This is standard .desktop behavior.
- **[Icon overwrite]** Copying the icon each time overwrites any manual customizations. Mitigation: this is consistent with how `--create-shortcut` already works — it's a creation command, not a configuration tool.
- **[XDG Desktop dir]** The code only checks `~/Desktop` and `~/Área de Trabalho`, ignoring `$XDG_DESKTOP_DIR`. Mitigation: acceptable for current scope; `$XDG_DESKTOP_DIR` detection can be added later if needed.
