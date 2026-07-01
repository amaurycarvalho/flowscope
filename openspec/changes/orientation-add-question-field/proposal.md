## Why

The OrientationPanel currently displays only Objetivo, Indicadores envolvidos, and Como interpretar — but it lacks the guiding question that each panel answers ("Responde a pergunta"). This question is already documented in `panels.md` but never surfaced in the UI. Adding it makes the orientation text self-contained and more useful: the user sees what question the panel answers before diving into indicators and interpretation.

## What Changes

- Insert the "Responde a pergunta" text into each sub-aba's orientation body in `app.py:_tab_content`, placed between "Objetivo" and "Indicadores envolvidos"
- The resulting body order becomes: **Objetivo → Responde a pergunta → Indicadores envolvidos → Como interpretar**
- No changes to `panels.md`, the OrientationPanel widget itself, or the quadrant summary append logic

## Capabilities

### New Capabilities

*(none — this is a refinement of existing UI content, not a new capability)*

### Modified Capabilities

- `gui-interface`: OrientationPanel content requirement is expanded to include "Responde a pergunta" (the question each panel answers) as a mandatory part of the explanatory text, between Objetivo and Indicadores envolvidos

## Impact

- **File modified:** `src/flowscope/presentation/gui/app.py` — `_tab_content` dict bodies updated
- **No API, dependency, or schema changes**
