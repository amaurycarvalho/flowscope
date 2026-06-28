## 1. Shared icon resolution helper

- [x] 1.1 Add `_resolve_icon_path()` function in `main.py` that handles dev (`__file__`) and frozen (`sys._MEIPASS`) modes
- [x] 1.2 Refactor `_set_icon()` in `app.py` to use the shared `_resolve_icon_path()`

## 2. Fix `_create_desktop_shortcut()` for correct paths

- [x] 2.1 Change `_create_desktop_shortcut()` to return `bool` (success/failure) instead of calling `sys.exit()`
- [x] 2.2 Resolve `Exec` to absolute path via `Path(sys.argv[0]).resolve()` and append ` --gui`
- [x] 2.3 Copy icon to `~/.local/share/icons/flowscope.png` (creating directory) before writing .desktop file
- [x] 2.4 Add `StartupNotify=true` to .desktop content
- [x] 2.5 Update `main()` to call `_create_desktop_shortcut()` and `sys.exit()` based on its return value

## 3. GUI shortcut button

- [x] 3.1 In `_build_top_bar()`, add conditional `_shortcut_btn` after "Copiar Dados" — visible only on Linux when no `~/Desktop/flowscope.desktop` or `~/Área de Trabalho/flowscope.desktop` exists
- [x] 3.2 Wire `_shortcut_btn` command to call `_create_desktop_shortcut()`, flash "Atalho criado!" on success, hide button; show error on failure

## 4. Update tests

- [x] 4.1 Update existing `test_linux_creates_shortcut` to verify Exec is absolute, `--gui` is present, Icon points to `~/.local/share/icons/`, and `StartupNotify=true`
- [x] 4.2 Add test for icon resolution: dev mode resolves via `__file__`, frozen mode resolves via `sys._MEIPASS`
- [x] 4.3 Add test for `_create_desktop_shortcut()` returning `False` on non-Linux instead of raising
- [x] 4.4 Add test for GUI button visibility logic (Linux with/without shortcut, non-Linux)
