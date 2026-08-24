# Knit Simulator

[Open Knit Simulator](../../demos/knit-simulator/demo.html)

## What it does

Visualizes knitting step by step as a wearable sweater. Each knitted row adds
one band of the garment, so you can watch the fabric construct itself from
the cast-on hem upward. Stitch counts only change when an instruction
explicitly changes them (yo, k2tog, ssk, bo) — the simulator never invents
operations.

## How to use it

1. **Instructions** -- Enter knitting instructions (one per line):
   - `co 10` -- Cast on 10 stitches
   - `k all` / `k10` -- Knit all (or 10) stitches
   - `p all` / `p10` -- Purl all (or 10) stitches
   - `k2 p2 across` or `* k2 p2` -- Repeat the sequence across the row
   - `yo` -- Yarn over (increase)
   - `k2tog` / `ssk` -- Decrease (works 2 stitches into 1)
   - `bo 10` -- Bind off 10 stitches
2. Click **Build Simulation**
3. Use the **Playback controls** to step through:
   - Play / Pause
   - Step forward / Step back
   - Reset to beginning
   - Speed selector (slow / normal / fast)

## Reading the results

- **Garment view** -- A front-facing sweater built row by row from the hem up:
  - Ribbed rows (rows that contain purls) show vertical ribbing texture
  - Plain rows show knit-stitch texture
  - The cast-on edge appears as a darker hem strip
  - Bind-off rows get a visible bind-off edge line
  - Sleeves, body, and neckline are revealed as construction progresses
- **Step log** -- Written record of each row: what was worked and the stitch
  count on the needle

## Example

```
co 10
k2 p2 across
k2 p2 across
k all
```

This casts on 10 stitches, works two rows of k2/p2 ribbing, then a stockinette
row. The stitch count stays at 10 for the whole simulation.

## Tips

- Use `across` (or a leading `*`) to repeat a stitch sequence across the row
- Watch the step log to see exactly which row is being added
- Rows that change the stitch count (yo, k2tog, ssk, bo) show their effect
  immediately in the log and the band texture
- Use speed controls to study complex stitch combinations
