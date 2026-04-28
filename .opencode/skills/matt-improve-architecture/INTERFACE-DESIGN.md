# Interface Design

When the user wants to explore alternative interfaces for a chosen deepening candidate, use this parallel sub-agent pattern.

Uses the vocabulary in [LANGUAGE.md](LANGUAGE.md) — **module**, **interface**, **seam**, **adapter**, **leverage**.

## Process

### 1. Frame the problem space

Before spawning sub-agents, write a user-facing explanation:
- The constraints any new interface would need to satisfy
- The dependencies it would rely on
- A rough illustrative code sketch to ground the constraints

### 2. Spawn sub-agents

Spawn 3+ sub-agents in parallel using the Task tool. Each must produce a **radically different** interface. Give each agent a different design constraint:

- Agent 1: "Minimize the interface — aim for 1-3 entry points max. Maximise leverage per entry point."
- Agent 2: "Maximise flexibility — support many use cases and extension."
- Agent 3: "Optimise for the most common caller — make the default case trivial."
- Agent 4 (if applicable): "Design around ports & adapters for cross-seam dependencies."

Each sub-agent outputs:
1. Interface (types, methods, params — plus invariants, ordering, error modes)
2. Usage example showing how callers use it
3. What the implementation hides behind the seam
4. Dependency strategy and adapters
5. Trade-offs

### 3. Present and compare

Present designs sequentially so the user can absorb each one, then compare by **depth**, **locality**, and **seam placement**.

After comparing, give your own recommendation: which design is strongest and why. If elements from different designs would combine well, propose a hybrid.
