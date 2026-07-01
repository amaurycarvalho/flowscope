## Context

The `_tab_content` dict in `app.py` maps `(main_tab, sub_tab)` → `(title, body)`. Each `body` string contains three sections separated by double newlines:
`Objetivo: ...` → `Indicadores envolvidos: ...` → `Como interpretar: ...`. The question each panel answers (`Responde a pergunta`) is documented in `panels.md` but is not part of the orientation text.

## Goals / Non-Goals

**Goals:**
- Add "Responde a pergunta" text to each of the 9 sub-aba orientation bodies
- Place it between "Objetivo" and "Indicadores envolvidos"
- Source the question text from `panels.md`

**Non-Goals:**
- No changes to `OrientationPanel` widget class
- No changes to `panels.md`
- No changes to the quadrant summary append logic in `_on_quadrant_summary`

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Where to insert | After "Objetivo" paragraph, before "Indicadores envolvidos" | Matches the cognitive flow: "what it does → what question it answers → what indicators → how to read it" |
| Format | `"Responde a pergunta: _<question>_\n\n"` | Matches existing formatting style of `Objetivo:` and `Indicadores envolvidos:` headers |
| Quadrantes special case | The question text is added to the base body; `_on_quadrant_summary` appends its summary after all existing content — no change needed | The append happens at the end of whatever body exists |

## Risks / Trade-offs

- **Text duplication risk** → The question text now lives in two places: `panels.md` (documentation source) and `app.py` (orientation content). If a question is updated in `panels.md` but not in `app.py`, they'll diverge. Acceptable for now — the source of truth for UI content is `app.py`.
