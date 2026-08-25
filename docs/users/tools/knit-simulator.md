# Knit Simulator

[Open Knit Simulator](../../demos/knit-simulator/demo.html)

## What it does

Visualizes knitting step by step as a wearable garment. Each knitted row adds
one band of the fabric, so you can watch it construct itself from the cast-on
edge onward. Three inputs are supported:

- **Manual instructions** — small patterns (up to ~24 cast-on stitches, up
  to 60 rows) render as a **swatch**: the live stitches hang as loops on a
  needle, and each completed row is drawn beneath the previous one as
  individual stitch glyphs — knit Vs vs purl bumps, so k2/p2 ribbing is
  obvious. Larger manual patterns render as a front-facing sweater built
  row by row from the hem up.
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

- **Swatch view** -- Small manual patterns (the default `co 10` example, or
  any pattern with a small cast-on) show a knitting needle with the live
  stitches as loops on it, and below it the completed fabric, one band per
  row. Each stitch is drawn individually: knit stitches as V shapes, purl
  stitches as horizontal bumps in a darker shade — so `k2 p2 across` shows
  as `V V · · V V · · …`. Row numbers sit to the left of each band, and when
  a row is worked its stitches slide down from the needle into the fabric.
- **Garment view** -- In manual mode, a front-facing sweater built row by row
  from the hem up (used when the pattern is too large for the swatch view):
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
- **Knitter's status line** -- For raglan plans, a two-line status above
  the garment always answers the knitter's question with real simulation
  values: `Yoke — Round 23 / 50` over `160 → 168 stitches (+8)`. The
  section, round-within-section, and the before → after stitch transition
  (per-round change in parentheses) all come straight from the executed
  steps.
- **Raglan geometry** -- The yoke visibly flares from the neckline to the
  underarms as the increase rounds are worked: the torso silhouette, raglan
  seams and outline all widen round by round, and one dot per completed
  increase round appears on each seam — the reason the garment widens is
  drawn, not just narrated. The sleeves only appear once their own sections
  start, so the sweater separates into body + sleeves instead of staying a
  rectangle.
- **Compact section progress** -- Instead of a giant list of rows, the raglan
  view shows one marker per garment section (`✓ Neck · ● Yoke 23/50 · ○ Body
  · ○ Left sleeve · ○ Right sleeve`), with the current section highlighted
  and its round counter shown.
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
