---
name: matt-improve-architecture
description: Find deepening opportunities in a codebase — refactors that turn shallow modules into deep ones. Use when user wants to improve architecture, find refactoring opportunities, consolidate tightly-coupled modules, or make a codebase more testable and AI-navigable.
---

# Improve Codebase Architecture

Surface architectural friction and propose **deepening opportunities** — refactors that turn shallow modules into deep ones. The aim is testability and AI-navigability.

## Glossary — see [LANGUAGE.md](LANGUAGE.md) for full definitions

- **Module** — anything with an interface and an implementation
- **Interface** — everything a caller must know to use the module (types, invariants, error modes, ordering, config)
- **Implementation** — the code inside
- **Depth** — leverage at the interface: a lot of behaviour behind a small interface
- **Seam** — where an interface lives; a place behaviour can be altered without editing in place
- **Adapter** — a concrete thing satisfying an interface at a seam
- **Leverage** — what callers get from depth
- **Locality** — what maintainers get from depth

Key principles:
- **Deletion test**: imagine deleting the module. If complexity vanishes, it was a pass-through.
- **The interface is the test surface.**
- **One adapter = hypothetical seam. Two adapters = real seam.**

This skill is _informed_ by the project's domain model — `CONTEXT.md` and any `docs/adr/`. See [CONTEXT-FORMAT.md](CONTEXT-FORMAT.md) and [ADR-FORMAT.md](ADR-FORMAT.md).

## Process

### 1. Explore

Read existing documentation first:
- `CONTEXT.md` (or `CONTEXT-MAP.md` + each `CONTEXT.md`)
- Relevant ADRs in `docs/adr/`

If any of these files don't exist, proceed silently — don't flag their absence.

Then explore the codebase and note where you experience friction:
- Where does understanding one concept require bouncing between many small modules?
- Where are modules **shallow** — interface nearly as complex as the implementation?
- Where have pure functions been extracted just for testability, but the real bugs hide in how they're called?
- Where do tightly-coupled modules leak across their seams?
- Which parts of the codebase are untested, or hard to test through their current interface?

Apply the **deletion test** to anything you suspect is shallow.

### 2. Present candidates

Present a numbered list of deepening opportunities. For each:
- **Files** — which files/modules are involved
- **Problem** — why the current architecture is causing friction
- **Solution** — plain English description of what would change
- **Benefits** — explained in terms of locality and leverage, and how tests would improve

**Use CONTEXT.md vocabulary for the domain, and LANGUAGE.md vocabulary for the architecture.**

### 3. Grilling loop

Once the user picks a candidate, drop into a grilling conversation. Walk the design tree — constraints, dependencies, the shape of the deepened module, what tests survive.

Side effects as decisions crystallize:
- **New domain term?** Add to `CONTEXT.md`
- **Sharpening a fuzzy term?** Update `CONTEXT.md`
- **User rejects with load-bearing reason?** Offer to record as ADR
- **Want alternative interfaces?** See [INTERFACE-DESIGN.md](INTERFACE-DESIGN.md)
