# Draw.io shapes and styles

Style strings are **`key=value`** segments separated by **`;`**. Order is usually irrelevant; duplicate keys — last wins.

## Style string pattern

```text
rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;
```

- **`whiteSpace=wrap`**: multi-line labels inside the shape.
- **`html=1`**: treat `value` as HTML (use sparingly for agents; plain text is safer).

## Basic shapes (built-in)

| Intent | Style hints |
|--------|-------------|
| Rectangle | `rounded=0;whiteSpace=wrap;html=1;` |
| Rounded rect | `rounded=1;whiteSpace=wrap;html=1;` |
| Ellipse / circle | `ellipse;whiteSpace=wrap;html=1;` — add `aspect=fixed;` for circle |
| Diamond (decision) | `rhombus;whiteSpace=wrap;html=1;` |
| Parallelogram | `shape=parallelogram;perimeter=parallelogramPerimeter;whiteSpace=wrap;fixedSize=1;size=20;` |
| Hexagon | `shape=hexagon;perimeter=hexagonPerimeter2;whiteSpace=wrap;size=25;fixedSize=1;` |
| Triangle | `triangle;whiteSpace=wrap;html=1;` |
| Cylinder (data store) | `shape=cylinder3;whiteSpace=wrap;boundedLbl=1;backgroundOutline=1;size=15;` |
| Cloud | `ellipse;shape=cloud;whiteSpace=wrap;html=1;` |
| Callout | `shape=callout;whiteSpace=wrap;html=1;` |

## Common visual properties

| Property | Notes |
|----------|--------|
| `fillColor` | `#RRGGBB` |
| `strokeColor` | Border |
| `fontColor` | e.g. `#333333` (works with diagramkit dark tweak) |
| `fontSize` | Numeric |
| `fontStyle` | `0` normal, `1` bold, `2` italic, `4` underline; combine by sum |
| `align` | `left`, `center`, `right` |
| `verticalAlign` | `top`, `middle`, `bottom` |
| `rounded` | `0` or `1` |
| `shadow` | `0` or `1` |
| `glass` | `0` or `1` (glass effect) |

## Swimlanes (process / zones)

```text
swimlane;startSize=20;html=1;
```

- **`startSize`**: title band height in px (often 20–40).
- Set `fillColor` / `strokeColor` for zone color; use **`fontStyle=1`** for lane titles.

## Groups and collapsible containers

- **Group**: vertex wrapping children; children reference **`parent="<group-id>"`**. Coordinates are **relative** to the group’s top-left.
- **Collapsible**: style may include **`collapsible=1`** on container shapes that support folding (editor-dependent); prefer plain swimlanes for predictable agent output.

## Icon / stencil shapes

- Library icons use **`shape=mxgraph.<library>.<icon>;`** (see `cloud-shapes.md`).
- Cisco-style network icons: `shape=mxgraph.cisco.*` (see infrastructure table in `SKILL.md`).

Keep palettes consistent: same fill/stroke for the same component type across the diagram.
