# Draw.io XML structure

Minimal mental model for generating valid `.drawio` / `.drawio.xml` files. Complements the inline examples in `SKILL.md`.

## Root: `<mxfile>`

- Wraps one or more pages. Common attrs: `host`, `modified`, `agent`, `version`, `type`.
- Each logical page is a child `<diagram>` (see multi-page in `layout.md`).

```xml
<mxfile host="diagramkit" modified="2026-01-01T00:00:00.000Z" type="device">
  <diagram id="page-1" name="Page-1">
    <!-- mxGraphModel -->
  </diagram>
</mxfile>
```

## Page: `<diagram>`

- **`id`**: Stable ID (ASCII, unique within file). Used by tools; keep deterministic.
- **`name`**: Human tab title shown in the editor.
- Contains exactly one `<mxGraphModel>`.

## Graph: `<mxGraphModel>`

- Holds diagram-wide settings: **`grid`**, **`gridSize`** (often `10`), **`pageWidth`**, **`pageHeight`**, **`dx`**, **`dy`**, `guides`, `connect`, `arrows`, `fold`, `page`, `pageScale`, `math`, `shadow`.
- Child must be `<root>`.

## Cells: `<root>` and `<mxCell>`

- **Root cell `id="0"`** — required; no parent. The graph root.
- **Default layer `id="1"`** — required; **`parent="0"`**. Most shapes/edges use **`parent="1"`** unless grouped (see below).
- Every other cell is an `<mxCell>` with unique `id` strings.

### Vertex (node)

- **`vertex="1"`**
- **`parent`** = layer id (`"1"`) or **container** cell id (swimlane, group).
- Label: **`value`** attribute (plain text or minimal HTML if `html=1` in style).
- **`style`**: semicolon-separated key=value (see `shapes.md`).
- Position/size: nested **`<mxGeometry ... as="geometry"/>`**.

```xml
<mxCell id="svc-a" value="Service A" style="rounded=1;whiteSpace=wrap;html=1;"
        vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="120" height="60" as="geometry"/>
</mxCell>
```

### Edge (connector)

- **`edge="1"`**
- **`source`** / **`target`**: string ids of vertex (or port) cells.
- **`parent`**: usually `"1"` (or same parent as endpoints when scoped).
- Geometry often **`relative="1"`** for automatic routing; waypoints in `edges.md`.

```xml
<mxCell id="e1" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;"
        edge="1" source="svc-a" target="svc-b" parent="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

## `<mxGeometry>`

- **Vertices**: `x`, `y`, `width`, `height` in diagram units (pixels at scale 1).
- **Edges**: often `relative="1"`; optional **`points`** or child **`Array`** of **`mxPoint`** for manual routing.
- **`as="geometry"`** is required on the geometry element.

## Layers and grouping

- **Layer**: any cell can act as a parent; children get coordinates **relative to that parent**.
- **`id="0"`** = graph root; **`id="1"`** = default layer — both are mandatory boilerplate.
- **Containers** (swimlane, group): vertex with larger geometry; child vertices use **`parent="<container-id>"`**.

Use semantic, stable ids (`api-gateway`, `subnet-private-a`) per quality rules in `SKILL.md`.
