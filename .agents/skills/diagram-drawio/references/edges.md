# Edges: routing, arrows, labels

All connectors are **`mxCell`** with **`edge="1"`**, **`source`**, **`target`**, and a **`style`** string (see inline examples in `SKILL.md`).

## Edge style: routing

| Style fragment | Behavior |
|----------------|----------|
| `edgeStyle=orthogonalEdgeStyle;` | Right-angle path (default for clean architecture diagrams) |
| `edgeStyle=elbowEdgeStyle;` | Single bend |
| `edgeStyle=entityRelationEdgeStyle;` | ER-style |
| `edgeStyle=isometricEdgeStyle;` | Isometric |
| `curved=1;` | Curved (often without orthogonal edgeStyle) |
| *(no edgeStyle)* | Straight segment between ports |

Combine with **`rounded=1;`** for rounded corners on orthogonal paths.

```xml
<mxCell id="e1" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;jettySize=auto;"
        edge="1" source="a" target="b" parent="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

## Manual waypoints

For fixed bends, put an **`<Array as="points">`** inside **`<mxGeometry>`** with **`relative="1"`** on the edge:

```xml
<mxGeometry relative="1" as="geometry">
  <Array as="points">
    <mxPoint x="200" y="100"/>
    <mxPoint x="200" y="220"/>
  </Array>
</mxGeometry>
```

Coordinates are usually **absolute** in the layer’s space (same as vertices on `parent="1"`). Adjust if the edge lives under a container parent.

## Labels on edges

- **Inline**: **`value`** on the edge **`mxCell`** (preferred for agents).
- **Separate label cell**: a child **`mxCell`** of the edge with **`vertex="1"`** and **`<mxGeometry relative="1" x="…" y="…">`** to offset text along the wire (editor-generated; use when precise placement matters).

Example (inline):

```xml
<mxCell id="e2" value="HTTPS" style="edgeStyle=orthogonalEdgeStyle;rounded=1;fontSize=11;"
        edge="1" source="c" target="d" parent="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

## Arrows

`startArrow=none;endArrow=classic;` — common values: `classic`, `block`, `open`, `oval`, `diamond` / `diamondThin`, `none`. ER: `ERmandOne`, `ERmany`, `ERoneToMany`, etc. (full list in `SKILL.md`).

## Line appearance

```text
strokeWidth=2;strokeColor=#666666;dashed=1;dashPattern=5 5;
```

| Effect | Style |
|--------|--------|
| Solid | omit `dashed` or `dashed=0` |
| Dashed | `dashed=1;dashPattern=5 5;` |
| Dotted | tight `dashPattern=2 2;` or similar |

Use **dashed edges** for optional/secondary relationships; **solid** for primary data/control flow.
