## Context

The entry point `main()` in `src/flowscope/presentation/main.py` currently falls through to `run_cli(args)` when no flags are given. The `--gui` flag must be explicitly passed to open the Tkinter window. This is counterintuitive since the GUI is the primary interaction mode.

The dispatch logic is a linear chain of `if` checks — there's no categorization of flags into "meta" (version, shortcut), "GUI", or "CLI data" modes.

## Goals / Non-Goals

**Goals:**
- Running `flowscope` without arguments opens the GUI
- All existing CLI flags (`--tickers`, `--vwap`, `--version`, `--create-shortcut`) continue to work exactly as before
- The `--gui` flag is retained for explicit use (desktop shortcut references it)

**Non-Goals:**
- No changes to the CLI argument definitions or help text
- No changes to the GUI or CLI code themselves — only the dispatch logic
- No removal of the `--gui` flag

## Decisions

### Decision: Categorize flags by "data" vs "meta"

Instead of a linear fallthrough, explicitly detect whether any data-processing flag was passed:

```
Meta flags:   --version, --create-shortcut
Data flags:   --tickers, --vwap
GUI flag:     --gui
```

**Rationale**: This makes the default behavior explicit and readable. Adding a future data flag (e.g. `--cvd`) means adding it to the data-flags condition — a one-line change.

**Alternative considered**: Checking `len(sys.argv) == 1` to detect no arguments. Rejected because it's fragile — a user might pass `--gui` explicitly and we'd want that to still work. Also, `--version` and `--create-shortcut` are legitimate single-flag invocations that should not trigger GUI.

### Decision: Keep `--gui` flag

The desktop shortcut (`flowscope.desktop`) currently executes `flowscope --gui`. Removing the flag would break it.

**Alternative considered**: Update the shortcut to `flowscope` (no flag). Rejected because it adds unnecessary churn to a working file.

## Risks / Trade-offs

- **[Breaking change]** Anyone relying on `flowscope` (no flags) for CLI output will need to add `--tickers` or `--vwap`. Since no default tickers or output exist today, this is likely a no-op for real users — but it's a behavioral change.
- **[Maintenance]** Future data flags must be added to the `has_cli_args` condition. Low risk — a single boolean expression in `main()`.
