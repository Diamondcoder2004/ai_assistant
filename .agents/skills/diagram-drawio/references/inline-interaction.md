# Inline Interaction Protocol

Use inline interaction in the agent conversation as the default and primary interaction method.

## Interaction Flags

Skills that support interactive workflows should prefer:

| Flag | Description |
|------|-------------|
| `--auto` | Skip human confirmations and proceed with recommended defaults |

When `--auto` is not set, interactions are rendered inline in conversation.

## Intent Confirmation

Render:

```text
## Confirm Intent

**Goal**: <one-line restatement>
**Reasoning**:
- <bullet 1>
- <bullet 2>
**Skills**: <skill list with rationale>
**Tools/MCPs**: <list with availability>
**Complexity**: <level> — <justification>

> Reply: **approve**, **edit: <changes>**, **simplify**, or **cancel**
```

## Approach Selection

Render:

```text
## Select Approach

1. **<Name>** — <summary> (Risk: <level>, Effort: <estimate>) [recommended]
2. **<Name>** — <summary> (Risk: <level>, Effort: <estimate>)
3. **<Name>** — <summary> (Risk: <level>, Effort: <estimate>)

> Reply: **1**, **2**, **3**, **mix: <instructions>**, or **discuss**
```

## Plan Approval

Render:

```text
## Approve Plan

Wave 1:
1. <task>
2. <task>

Wave 2:
3. <task>

> Reply: **approve**, **add: <task>**, **remove: <number>**, or **cancel**
```

## Review Findings

For review-style triage:

```text
## Review Findings

> Actions: a accept | r reject | e edit | s skip
> Example: a-1,4 r-2 e-3 s-5
> Also: a-all | details <N> | done
```

Process edit actions one by one, regenerate, reconfirm, and continue until all items are resolved.

## Progress Dashboard

For long execution, show checkpoint-style inline progress:

```text
## Progress

Wave 1: [completed]
Wave 2: [running]
Wave 3: [pending]
```
