## Context

`OrientationPanel.set_content(title, body)` currently takes `body` as a plain string and inserts it into a `tk.Text` widget with no formatting. The `tk.Text` widget natively supports rich text via tags — but nothing uses them. Meanwhile, `_tab_content` in `app.py` stores each body as a f-string with sections like `Objetivo:`, `Responde a pergunta:`, `Indicadores envolvidos:`, `Como interpretar:`.

## Goals / Non-Goals

**Goals:**
- Refactor `set_content` to accept structured content with formatting tags
- Apply bold to section headers (`Objetivo:`, `Responde a pergunta:`, etc.)
- Apply italic to question text
- Keep plain text for descriptions and interpretation
- Maintain full backward compatibility for the Quadrantes summary append

**Non-Goals:**
- No Markdown parser
- No color or font-size changes
- No changes to `panels.md`
- No new external dependencies

## Decisions

### New `set_content` signature

```
set_content(title: str, body: list[tuple[str, str]]) -> None
```

Each tuple is `(text_segment, tag_name)`. Tag name is one of `"bold"`, `"italic"`, or `""` (plain).

### Tag configuration in `__init__`

Two `tag_config` calls are added to the `tk.Text` widget:

```python
self._text.tag_config("bold", font=("TkDefaultFont", 9, "bold"))
self._text.tag_config("italic", font=("TkDefaultFont", 9, "italic"))
```

The `"bold"` tag reuses the same font as the title label, keeping visual consistency.

### Body content structure

Each sub-aba body becomes a list. Example for VWAP:

```python
body = [
    ("Objetivo: ", "bold"),
    ("Identificar o preço médio ponderado...\n\n", ""),
    ("Responde a pergunta: ", "bold"),
    ("\"Quem está acima do preço justo e quem está abaixo?\"\n\n", "italic"),
    ("Indicadores envolvidos: ", "bold"),
    ("VWAP (preço médio ponderado)...\n\n", ""),
    ("Como interpretar: ", "bold"),
    ("O VWAP é a referência...", ""),
]
```

### Quadrantes summary append

`_on_quadrant_summary` currently appends `f"{body}\n\n---\n\n{summary}"`. Since `body` is now a list, the summary text is appended as an additional tuple `("\n\n---\n\n" + summary, "")` at the end of the body list before passing to `set_content`.

### Tag name choice

Using `""` (empty string) for plain text avoids the need for a special `None` check — the inserter simply skips `tag_config` when tag is empty.

### Risks / Trade-offs

- **Larger `_tab_content` dict** → Each body grows from 3-5 string lines to 8-16 tuple lines. More verbose but more explicit. Trade-off accepted for readability gain in the UI.
- **Summary append coupling** → `_on_quadrant_summary` now manipulates a list instead of a string. Slightly more complex but still straightforward: `body.append(("\n\n---\n\n" + summary, ""))`.
