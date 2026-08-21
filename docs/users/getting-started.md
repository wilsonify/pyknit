# User Guide

Welcome to pyKnit's interactive knitting tools.

## What can I do with pyKnit?

pyKnit provides free, browser-based tools for common knitting calculations.
No installation, no account, no data leaves your device.

### Plan a project

- **[Raglan Sweater Planner](../../demos/raglan-sweater/demo.html)** -- Plan a complete top-down raglan from your gauge and measurements
- **[Sock Calculator](../../demos/sock-calculator/demo.html)** -- Get a custom-fit sock plan for your foot
- **[Hat Crown Planner](../../demos/hat-crown/demo.html)** -- Plan decrease rounds for a hat crown
- **[Pi Shawl Planner](../../demos/pi-shawl/demo.html)** -- Find doubling rounds for a pi shawl
- **[Shawl Shapes](../../demos/shawl-shapes/demo.html)** -- Generate instructions for crescent, triangle, square, or rectangle shawls
- **[Sleeve Decreases](../../demos/sleeve-decreases/demo.html)** -- Plan evenly-spaced decrease rows for tapered sleeves

### Shape your knitting

- **[Even Shaping](../../demos/even-shaping/demo.html)** -- Space increases or decreases evenly across a round or row

### Choose your materials

- **[Yarn Advisor](../../demos/yarn-advisor/demo.html)** -- Get fiber and yarn weight recommendations for your project
- **[Needle Advisor](../../demos/needle-advisor/demo.html)** -- Find the right needle size, type, and cable length

### Calculate and convert

- **[Gauge Conversion](../../demos/gauge-conversion/demo.html)** -- Convert stitch and row counts between different gauges
- **[Yarn and Time Estimator](../../demos/yarn-estimator/demo.html)** -- Estimate yardage, grams, and knitting time

### Patterns and charts

- **[Chart Renderer](../../demos/chart-renderer/demo.html)** -- Type knitting abbreviations and see a stitch chart
- **[Knit Simulator](../../demos/knit-simulator/demo.html)** -- Watch knitting happen step by step

## Getting started

1. Open any tool from the links above
2. Wait 30-60 seconds on first visit (the Python runtime downloads to your browser)
3. Fill in the form fields
4. Click the action button
5. Read your results

No account needed. No data leaves your browser.

## First visit

The first time you use any tool, pyKnit downloads about 20 MB of packages to your
browser. This takes 30-60 seconds. After that, subsequent visits load in 5-10
seconds.

## Recommended workflows

### Planning a sweater

```
Choose yarn -> Yarn Advisor
     |
Choose needles -> Needle Advisor
     |
Knit a gauge swatch
     |
Enter gauge into Raglan Sweater Planner
     |
Follow the generated plan
```

### Knitting custom socks

```
Measure your foot
     |
Enter gauge into Sock Calculator
     |
Get your custom sock plan
     |
Adjust for fit
```

### Resizing a pattern

```
Knit a gauge swatch
     |
Compare your gauge to the pattern gauge
     |
Use Gauge Conversion to adjust measurements
     |
Check shaping with Even Shaping
```

## Troubleshooting

### Tools won't load

- **Wait longer** -- First visit takes 30-60 seconds
- **Check your browser** -- Use Chrome 57+, Firefox 52+, Safari 14.1+, or Edge 79+
- **Check your connection** -- First visit needs internet to download packages

### Results look wrong

- **Check your gauge** -- Make sure stitches and rows per inch are correct
- **Check your units** -- Some tools expect inches, others centimeters
- **Read the warnings** -- Tools show warnings when inputs seem unusual

### Buttons don't work

- **Hard refresh** -- Press Ctrl+Shift+R (or Cmd+Shift+R on Mac)
- **Clear cache** -- Open browser developer tools (F12), go to Application, clear storage
