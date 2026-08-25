# Knit Simulator

[Open Knit Simulator](../../demos/knit-simulator/demo.html)

## What it does

Visualizes knitting step by step as a wearable garment. Each knitted row adds
one band of the fabric, so you can watch it construct itself from the cast-on
edge onward. Three inputs are supported:

- **Manual instructions** — a front-facing sweater built row by row from the
  hem up.
- **Sock Calculator** — run the [Sock Calculator](../../demos/sock-calculator/demo.html), click
  **Simulate sock**, and the simulator shows the calculated sock being built
  round by round (cuff, leg, heel flap and turn, gusset, foot, toe). The
  calculator's pattern is the single source of truth: cast-on stitches,
  round count, and every decrease are taken straight from it, never
  re-derived or invented.
- **Raglan Sweater Planner** — run the
  [Raglan Sweater Planner](../../demos/raglan-sweater/demo.html), click **Simulate sweater**,
  and the Planner's generated instructions fill the instructions field
  exactly as generated; the simulator then executes those same instructions.
  The sweater is built top-down (collar first), and the cast-on, collar,
  raglan increase schedule, body rounds, hem, sleeve decreases and cuffs all
  match the Planner's numbers. Edits to the field are used on the next
  Build.

In all modes, stitch counts only change when the pattern explicitly changes
them (yo, k2tog, ssk, bo, or the Planner's shaping rounds).

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

- **Garment view** -- In manual mode, a front-facing sweater built row by row
  from the hem up:
  - Ribbed rows (rows that contain purls) show vertical ribbing texture
  - Plain rows show knit-stitch texture
  - The cast-on edge appears as a darker hem strip
  - Bind-off rows get a visible bind-off edge line
  - Sleeves, body, and neckline are revealed as construction progresses
  - In sock mode, a bent sock schematic (cuff, leg, heel, foot, toe) is
    revealed along the knitting direction; the cuff shows ribbing, the heel
    region a slip-stitch texture, and decrease rounds appear as small marks
  - Raglan plans are revealed top-down and are section-aware: the neckline
    (cast-on + collar + neck increase) appears first, the yoke widens with
    each raglan increase round (visible raglan seam lines), then the body
    and hem grow downward — and the sleeves only appear once their own
    sections start, so the sweater visibly separates into body + sleeves
    instead of staying a rectangle
  - A summary box shows the size, cast-on stitches, ankle stitches and round
    count when the sock plan comes from the Sock Calculator; for raglan
    plans it shows the neck, yoke, bust, arm and cuff counts from the
    Planner
- **Knitter's status line** -- For raglan plans, a line above the garment
  always answers the knitter's question with real simulation values:
  `Phase: Yoke · Row 23 / 58 · Stitches: 136 · Raglan increase (+8)`. The
  phase, row-within-section, stitch count and operation all come straight
  from the executed steps.
- **Compact section progress** -- Instead of a giant list of rows, the raglan
  view shows one marker per garment section (`✓ Neckline · → Yoke · ○ Body
  · ○ Left sleeve · ○ Right sleeve`), with the current section highlighted.
- **Step log** -- Written record of each row/round: what was worked and the
  stitch count on the needle. It is collapsed into a *Step log* disclosure by
  default so the detailed rows don't overwhelm the garment view; open it to
  see every step.

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

- From the Sock Calculator, click **Simulate sock**, or from the Raglan
  Sweater Planner click **Simulate sweater**, to hand their computed pattern
  to this simulator; the clear buttons return to the default manual pattern
- Use `across` (or a leading `*`) to repeat a stitch sequence across the row
- Watch the step log to see exactly which row is being added
- Rows that change the stitch count (yo, k2tog, ssk, bo) show their effect
  immediately in the log and the band texture
- A row that tries to work more stitches than are on the needle is reported
  as a warning instead of silently producing a misleading garment
- Use speed controls to study complex stitch combinations
- For a raglan plan, editing the instructions field and clicking **Build
  Simulation** re-runs the simulation on exactly your edited text (the
  Planner's sections are dropped once the text no longer matches)
