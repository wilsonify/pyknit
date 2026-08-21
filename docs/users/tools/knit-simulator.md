# Knit Simulator

[Open Knit Simulator](../../demos/knit-simulator/demo.html)

## What it does

Visualizes knitting step by step. Watch how each stitch (knit, purl, yarn over,
k2tog, ssk) builds fabric row by row.

## How to use it

1. **Instructions** -- Enter knitting instructions (one per line):
   - `co 10` -- Cast on 10 stitches
   - `k10` -- Knit 10 stitches
   - `p10` -- Purl 10 stitches
   - `yo` -- Yarn over
   - `k2tog` -- Knit 2 together (right-leaning decrease)
   - `ssk` -- Slip, slip, knit (left-leaning decrease)
   - `bo 10` -- Bind off 10 stitches
2. Click **Simulate**
3. Use the **Playback controls** to step through:
   - Play / Pause
   - Step forward / Step back
   - Reset to beginning
   - Speed slider (slow / normal / fast)

## Reading the results

- **Current needle view** -- The stitch currently being worked, with a marker showing position
- **Fabric view** -- The accumulated fabric as a colored grid:
  - Blue = knit stitches
  - Yellow = purl stitches
  - Green = yarn overs
  - Gray = bound off
- **Step log** -- Written record of each operation

## Example

```
co 10
k10
p10
k10
p10
```

This creates a 5-row stockinette rectangle (cast on, then alternating knit and purl rows).

## Tips

- Watch the fabric view to see how decreases pull fabric left or right
- Yarn overs create holes -- useful for lace patterns
- Use speed controls to study complex stitch combinations
