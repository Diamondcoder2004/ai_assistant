# Layout and pages

Draw.io XML has **no built-in auto-layout in the file format** — hierarchy and positions are **explicit `x,y,width,height`**. Use predictable grids and patterns so diagrams stay readable when edited in the app.

## Mental layout types (manual placement)

| Pattern | Placement rule | Good for |
|---------|------------------|----------|
| Hierarchical top-down | Rows by tier; increase `y` between layers | Architecture, org charts |
| Hierarchical left-right | Columns by layer; increase `x` | Sequence, swimlane-aligned tiers |
| Left-to-right pipeline | Fixed `y`, increase `x` | Data/CI flows |
| Tree | Children below parent, centered subtrees | Taxonomies |
| Radial | Nodes on a circle (manual trig or copy positions) | Hub-and-spoke |
| Organic | Irregular but non-overlapping | Sketches (higher effort) |

**Editor (auto-layout)**: Arrange → **Layout** in diagrams.net offers **Hierarchical**, **Tree**, **Radial**, **Organic**, etc. They reposition selected shapes; the saved file still stores **explicit geometry** after layout. Agents should **compute coordinates** unless relying on a human to run layout in the app.

## Grid

- Default **10px** grid: align `x`, `y`, `width`, `height` to multiples of **`gridSize`** (typically `10`) from `<mxGraphModel grid="1" gridSize="10">`.
- Keeps connectors orthogonal and edits clean.

## Multi-page files

Separate **`<diagram>`** elements, each with its **own** `<mxGraphModel>` and **`<root>`** boilerplate (`id="0"`, `id="1"`).

```xml
<mxfile host="diagramkit">
  <diagram id="overview" name="01 — System overview">
    <mxGraphModel>...</mxGraphModel>
  </diagram>
  <diagram id="data" name="02 — Data layer">
    <mxGraphModel>...</mxGraphModel>
  </diagram>
</mxfile>
```

### Page naming (documentation)

- Prefix with **order**: `01 —`, `02 —` so tabs sort logically.
- Use **short, task-specific** names: `Network`, `Auth flow`, `Deployment`.
- Split when a page exceeds ~**20–25** elements (`SKILL.md` quality rule).

## Swimlanes for processes

- Use **`swimlane;startSize=…`** containers; place steps as children with **relative** geometry.
- One swimlane per actor or phase; flow **orthogonal** edges between steps.

## Page size

Set on **`<mxGraphModel>`**:

- **Custom**: `pageWidth`, `pageHeight` (e.g. `1200` × `900`).
- **Paper**: approximate pixel sizes — **A4** ~`827`×`1169` at 96 DPI scale depends on app; use project defaults or match existing diagrams.
- **Letter** ~`850`×`1100` — verify in editor if print fidelity matters.

Export/print margins are editor-specific; for repo assets, **SVG/PNG** from `diagramkit render` is usually sufficient.

## Consistency checklist

1. Same **node size** per tier (e.g. 120×60).
2. Same **horizontal/vertical gap** between siblings.
3. **One direction** for primary flow (LR or TB), not mixed without reason.
4. **Color legend** implicit via repeated fills (see Color Combinations in `SKILL.md`).
