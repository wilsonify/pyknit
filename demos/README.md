# pyKnit Browser Demos

Interactive knitting tools that run Python in your browser via WebAssembly.
No installation required.

**[Open the landing page](index.html)**

## Quick start

```bash
cd demos
make setup serve
# Open http://localhost:8000/index.html
```

## Available tools

| Category | Tool | Description |
|----------|------|-------------|
| Plan | [Raglan Sweater](raglan-sweater/demo.html) | Top-down raglan sweater planner |
| Plan | [Sock Calculator](sock-calculator/demo.html) | Custom-fit sock plan |
| Plan | [Hat Crown](hat-crown/demo.html) | Crown decrease schedule |
| Plan | [Pi Shawl](pi-shawl/demo.html) | Pi shawl increase rounds |
| Plan | [Shawl Shapes](shawl-shapes/demo.html) | Shawl instructions by shape |
| Plan | [Sleeve Decreases](sleeve-decreases/demo.html) | Even decrease spacing |
| Shape | [Even Shaping](even-shaping/demo.html) | Space increases/decreases evenly |
| Calculate | [Gauge Conversion](gauge-conversion/demo.html) | Convert measurements between gauges |
| Calculate | [Yarn & Time Estimator](yarn-estimator/demo.html) | Estimate yardage and time |
| Materials | [Yarn Advisor](yarn-advisor/demo.html) | Yarn and fiber recommendations |
| Materials | [Needle Advisor](needle-advisor/demo.html) | Needle size and type recommendations |
| Charts | [Chart Renderer](chart-renderer/demo.html) | Render knitting instructions as a chart |
| Charts | [Knit Simulator](knit-simulator/demo.html) | Watch knitting step by step |

Full documentation: [User guide](../docs/users/getting-started.md)

## Architecture

Each demo has two parts:

1. **Python module** (`pyknit/pyscript/_demos/<name>.py`) -- compute and render logic
2. **HTML page** (`demos/<name>/demo.html`) -- form and display

The shared helper (`pyknit/pyscript/_assets/shared.py`) wires forms to compute
functions and manages status banners.

## Development

```bash
# Run tests
python -m pytest test/unit/test_pyscript_demos.py -x -q

# Rebuild wheel after changing pyknit source
cd demos && make wheel

# Validate all demos
for demo in */demo.html; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/$demo")
  echo "$code $demo"
done
```

## Creating a new demo

See [creating a demo guide](../docs/developers/creating-a-demo.md).

## Troubleshooting

See [admin troubleshooting](../docs/admins/troubleshooting.md).
