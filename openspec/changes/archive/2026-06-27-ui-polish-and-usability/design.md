## Context

FlowScopeGUI is a ~200-line monolithic `tk.Tk` subclass. The entire UI is built in `__init__()` with direct geometry management. Widgets use raw `tk` (not `ttk`). Spacing constants are scattered (`padx=2,4,5,10`). There is no loading protection, no keyboard binding, no tooltip system, no preferences persistence, and the icon slot is empty (`src/flowscope/icons/__init__.py` is empty).

This design covers ~25 polish improvements that touch the presentation layer only — no domain, application, or infrastructure changes.

## Goals / Non-Goals

**Goals:**
- Prevent double-clicks and accidental UI interaction during data loading
- Provide immediate visual feedback for every user action
- Make the app feel responsive and professional with minimal structural change
- Persist window layout across sessions
- Add keyboard shortcuts for power users (avoiding system conflicts)
- Provide context-sensitive help via tooltips

**Non-Goals:**
- No layout overhaul or visual redesign (widget positions stay identical)
- No threading or async (loading is already synchronous; we just guard the UI)
- No new external dependencies (ttk is stdlib, tooltips are pure tkinter bindings)
- No chart rendering changes

## Decisions

### 1. Loading guard pattern
Extract loading state into paired methods instead of inline flag:

```
_enter_loading_state()   → disable button, disable DateEntry, cursor wait, status "⏳"
_exit_loading_state()    → enable all, restore cursor, update status
```

Called via try/finally in `_on_load_data`. No new threading needed.

### 2. Icon handling
Check `src/flowscope/icons/` for platform-appropriate file:
- Windows: `flowscope.ico` → `iconbitmap()`
- Linux: `flowscope.png` → `wm_iconphoto()`

If missing, silently skip (no crash). This keeps the app functional without icon assets.

### 3. Tooltip system
Standalone `ToolTip` class in `presentation/gui/widgets/tooltip.py`:

```python
class ToolTip:
    def __init__(self, widget, text):
        self._widget = widget
        self._text = text
        widget.bind("<Enter>", self._enter)
        widget.bind("<Leave>", self._leave)
```

Creates a transient `tk.Toplevel` positioned near the widget on hover. Pure tkinter, no deps.

### 4. Preferences persistence
JSON file at `~/.flowscope/config.json`:

```json
{
  "last_date": "2026-06-25",
  "last_chart": "vwap",
  "window_geometry": "1536x864+192+108",
  "sash_positions": [300, 200]
}
```

Saved on window close (`WM_DELETE_WINDOW` protocol) and on chart/date changes. Loaded in `__init__`.

### 5. Keyboard shortcuts
Bound via `bind_all` on the root window:

| Shortcut | Action | Note |
|---|---|---|
| `<Return>` | Carregar | Only when DateEntry focused (implicit via focus) |
| `<Control-c>` | Copiar Dados | Standard copy — safe on all platforms |
| `<F5>` | Recarregar | Refreshes current date |

Explicitly NOT using Ctrl+Shift+C (conflicts with terminal paste on Linux).

### 6. Statusbar with auto-clear
Internal counter via `after()`:

```python
def _flash_status(self, msg: str, icon: str = "✓", clear_ms: int = 2500):
    self._status_var.set(f"{icon} {msg}")
    self.after(clear_ms, lambda: self._set_status("Pronto."))
```

Icons: `✓` (success), `⏳` (loading), `⚠` (warning), `ℹ` (info).

### 7. Context menu on ticker list
`tk.Menu(tearoff=0)` bound to `<Button-3>`. Options:
- Copiar ticker selecionado
- Remover ticker do filtro
- Selecionar todos
- Limpar seleção

### 8. LabelFrame grouping
Wrap existing selector frame in `ttk.LabelFrame` and action buttons frame in `ttk.LabelFrame`. Minimal parent rearrangement — existing children are reparented into the LabelFrame.

### 9. Dynamic window title
Update `self.title()` after load and after filter changes:

```
f"FlowScope — {ref_date} — {n} ativos"
f"FlowScope — {ref_date} — {filtered}/{total} ativos"
```

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| Icon file missing at expected path | Graceful skip — app works without icon |
| Preferences JSON corrupted | Try/except in load, reset to defaults on parse error |
| `after()` callbacks race on rapid clicks | Cancel pending timer via `after_cancel()` before setting new one |
| `ttk.LabelFrame` changes visual appearance slightly | Style with `ttk.Style().configure('TLabelframe', ...)` to match current look |
| Systray icon not appearing on some Linux WMs | `wm_iconphoto()` works on most; X11 may need `-type normal` (already set) |
