# Project Guidelines (Common to All Skills)

These guidelines apply across all DevKit skills. When updating the canonical copy, propagate the change so every skill keeps its own local copy.

---

## Agentic Team Dispatch

See `references/agentic-teams.md` for full team shapes. Key rules:

- Non-trivial tasks (Medium+ complexity) must use parallel child agents
- Each agent gets a focused brief and isolated context
- Results are merged with duplicate removal and confidence scoring
- Agent count scales with complexity: Small=1, Medium=2-3, Large=4-5

## Output Conventions

- Default output format is markdown
- All output-producing skills support `--verbosity short|standard|detailed`
- Default verbosity is `standard`; PR comments use severity-based auto-selection
- See `references/output-format-modes.md` for mode templates and selection rules

## Preflight Protocol

Every skill must run preflight before execution:
```
python3 ${CLAUDE_SKILL_DIR}/scripts/preflight.py ${CLAUDE_SKILL_DIR}
```

## Self-Review Principles

Phase 5 (Validate & Learn) applies to all non-trivial output:
- Up to 10 iterations of review/fix/simplify/re-review
- Check: correctness, completeness, consistency, readability
- For code: run tests, check types, verify no regressions
- For docs: check structure, cross-references, accuracy

## Complexity-Adaptive Phase Skipping

| Complexity | Files | Phase 0 | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 |
|---|---|---|---|---|---|---|---|
| Trivial | 1 | inline | skip | skip | skip | direct | quick |
| Small | 2-3 | inline | lite | inline | brief | execute | verify |
| Medium | 4-8 | full | full | full | full | execute | full |
| Large | >8 | full + PE | full | full | full | phased | full |

## Description Marker Convention

All skill descriptions must be prefixed with type and area markers:

```
"[full] [review] Use when..."
"[partial] [audit] Use when..."
"[helper] [guidelines] Helper skill that..."
"[orchestrator] [pipeline] Use when..."
```

Types: `full`, `partial`, `helper`, `orchestrator`
Areas: `review`, `audit`, `develop`, `write`, `plan`, `diagram`, `spec`, `project`, `session`, `agent`, `design`, `research`, `setup`, `utility`
