## Why

The OrientationPanel currently displays all content as plain text — headers, questions, and terms like CLV and VWAP all look the same. This makes it harder for users to scan and parse the orientation text quickly. Adding native rich text formatting (bold headers, italicized questions) improves readability without external dependencies.

## What Changes

- `OrientationPanel.set_content()` changes signature from `(title: str, body: str)` to `(title: str, body: list[tuple[str, str]])` where each tuple is `(text, tag_name)`
- `_tab_content` in `app.py` is refactored: each body becomes a list of `(segment, tag)` tuples
- `OrientationPanel` applies `tk.Text` tags for `"bold"`, `"italic"`, and `""` (plain) formatting
- All 9 sub-aba bodies are updated to use the new format
- `_on_quadrant_summary` in `app.py` is updated to work with the new body format

## Capabilities

### New Capabilities

*(none)*

### Modified Capabilities

- `gui-interface`: OrientationPanel content format changes from plain string to structured list of tagged segments; `set_content` signature updated to support rich text formatting

## Impact

- **Modified:** `src/flowscope/presentation/gui/widgets/orientation_panel.py` — tag configs, `set_content` signature
- **Modified:** `src/flowscope/presentation/gui/app.py` — all 9 bodies in `_tab_content`, `_on_quadrant_summary`
- **No new dependencies**
- **No API changes outside the OrientationPanel**
