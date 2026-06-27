## Why

The GUI currently works but feels raw — no loading protection, no keyboard shortcuts, no visual feedback for actions, and inconsistent spacing. These 25+ small roughnesses accumulate into a perception of an unfinished tool. A focused polish pass dramatically increases perceived quality and daily productivity without changing any core functionality.

## What Changes

- App icon set on the window for taskbar display (`.ico` on Windows, `.png` on Linux)
- Controls disabled during loading (Carregar button + DateEntry) with wait cursor
- Statusbar with Unicode state icons (✓ ⏳ ⚠ ℹ) and auto-clearing timed messages
- Ticker counter label updated live (e.g. "Tickers (37)" / "Exibindo 42 de 300")
- Show currently loaded reference date on the UI
- Confirmation flash on copy actions ("✓ Dados copiados") auto-clearing after 2.5s
- Keyboard shortcuts: Enter→Carregar, Ctrl+C→Copiar Dados, F5→Recarregar (avoids system conflicts)
- Double-click on ticker list filters/selects that ticker
- Tooltips on all controls (indicators, buttons, chart selector)
- Hand cursor (`hand2`) on all interactive controls
- Initial keyboard focus on DateEntry
- Chart type selector wrapped in a LabelFrame titled "Visualização"
- Bottom action buttons wrapped in a LabelFrame titled "Exportação"
- Consistent padding constants (`PAD_SMALL=4`, `PAD=8`, `PAD_LARGE=12`) replacing ad-hoc values
- ttk.Separator between export buttons
- Internal button padding (`ipadx=8`, `ipady=2`)
- Dynamic chart title label above the chart area (e.g. "VWAP Histogram")
- Empty-state message when filter removes all tickers
- User-friendly error display (short message + expandable details)
- Filtered/Total count in status (e.g. "Exibindo 42 de 300 ativos")
- Persist window geometry and PanedWindow sash position to `~/.flowscope/config.json`
- Dynamic window title: "FlowScope — YYYY-MM-DD — N ativos"
- Animated processing indicator using `after()` (spinning dots)
- Context menu (right-click) on ticker list: Copy, Remove, Select All, Clear
- Subtle toolbar border (GROOVE) around action buttons
- Consistent use of `ttk` themed widgets where possible

## Capabilities

### New Capabilities
- `ui-polish`: All UI/UX polish improvements — loading states, status feedback, shortcuts, tooltips, cursors, focus, layout grouping, padding, separators, window title, context menu, empty states, friendly errors

### Modified Capabilities
- `gui-interface`: Numerous upgrades to the existing GUI — loading guard, icon, keyboard shortcuts, double-click filter, status feedback, ticker counter, date display, copy confirmation, persistent layout

## Impact

- `src/flowscope/presentation/gui/app.py` — major changes to FlowScopeGUI class
- `src/flowscope/presentation/gui/widgets/ticker_list.py` — context menu, double-click, counter
- New file: `src/flowscope/presentation/gui/widgets/tooltip.py` — tooltip utility
- New file: `src/flowscope/presentation/gui/config.py` — preferences persistence
- `src/flowscope/icons/` — icon file resolution (currently empty, needs asset)
- No new external dependencies (ttk is stdlib, tooltips are pure tkinter)
