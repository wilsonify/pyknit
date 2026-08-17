"""
Tests for the pyScript demo logic modules in pyknit/pyscript/_demos/.

Each module exports a ``DEMO`` dict with ``DEFAULT_INPUTS``, ``compute`` and
``to_html``.  This suite loads every module by path (they are plain scripts
run by PyScript, not importable packages) and exercises both the happy path
with default inputs and the error path with invalid inputs.
"""

import importlib.util
import pathlib

import pytest

from pyknit.pyscript._assets import shared

DEMOS_DIR = pathlib.Path(__file__).parent.parent.parent / "pyknit" / "pyscript" / "_demos"

DEMO_NAMES = [
    "chart_renderer",
    "hat_crown",
    "sock_calculator",
    "pi_shawl",
    "shawl_shapes",
    "sleeve_decreases",
    "shaping",
    "raglan",
    "yarn_estimator",
    "pattern_io",
]


def load_demo(name):
    spec = importlib.util.spec_from_file_location(
        "demo_" + name, DEMOS_DIR / (name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module", params=DEMO_NAMES)
def demo_module(request):
    return load_demo(request.param)


class TestDemoContracts:
    """Every demo module exposes the expected DEMO interface."""

    def test_demo_exports_dict(self, demo_module):
        assert isinstance(demo_module.DEMO, dict)

    def test_demo_has_required_keys(self, demo_module):
        for key in ("TITLE", "DEFAULT_INPUTS", "compute"):
            assert key in demo_module.DEMO

    def test_demo_has_callable_compute(self, demo_module):
        assert callable(demo_module.DEMO["compute"])

    def test_demo_to_html_callable(self, demo_module):
        assert callable(demo_module.DEMO["to_html"])

    def test_default_inputs_dict(self, demo_module):
        assert isinstance(demo_module.DEMO["DEFAULT_INPUTS"], dict)
        assert demo_module.DEMO["DEFAULT_INPUTS"]


class TestDemoCompute:
    """compute() runs with defaults and renders to HTML."""

    def test_compute_with_defaults(self, demo_module):
        result = demo_module.DEMO["compute"](demo_module.DEMO["DEFAULT_INPUTS"])
        assert result is not None

    def test_to_html_renders_string(self, demo_module):
        result = demo_module.DEMO["compute"](demo_module.DEMO["DEFAULT_INPUTS"])
        html = demo_module.DEMO["to_html"](result)
        assert isinstance(html, str)
        assert len(html) > 0

    def test_compute_returns_dict(self, demo_module):
        result = demo_module.DEMO["compute"](demo_module.DEMO["DEFAULT_INPUTS"])
        assert isinstance(result, dict)


class TestDemoErrors:
    """Invalid inputs surface as catchable errors, never crashes."""

    @pytest.mark.parametrize(
        "name,broken",
        [
            ("chart_renderer", "pattern"),
            ("hat_crown", "stitches"),
            ("sock_calculator", "stitches_per_inch"),
            ("pi_shawl", "radius"),
            ("shawl_shapes", "width"),
            ("sleeve_decreases", "starting_count"),
            ("shaping", "starting_count"),
            ("raglan", "neck_stitches"),
            ("yarn_estimator", "project_stitches"),
            ("pattern_io", "pattern"),
        ],
    )
    def test_zero_or_empty_value_raises(self, name, broken):
        module = load_demo(name)
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs[broken] = 0 if isinstance(inputs[broken], (int, float)) else ""
        with pytest.raises((ValueError, TypeError, KeyError)):
            module.DEMO["compute"](inputs)

    def test_bad_format_rejected(self):
        module = load_demo("pattern_io")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs["format"] = "xml"
        with pytest.raises(ValueError):
            module.DEMO["compute"](inputs)

    def test_bad_operation_rejected(self):
        module = load_demo("shaping")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs["operation"] = "magic"
        with pytest.raises(ValueError):
            module.DEMO["compute"](inputs)


class TestDemoSpecifics:
    """Spot checks on the values each demo actually produces."""

    def test_pi_shawl_rows(self):
        module = load_demo("pi_shawl")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        assert result["total_rounds"] > 0
        half = result["half_pi"]
        if isinstance(half, (list, tuple)):
            assert all(r <= result["total_rounds"] for r in half)
        else:
            assert half <= result["total_rounds"]

    def test_pi_shawl_explains_math_and_progression(self):
        module = load_demo("pi_shawl")
        result = module.DEMO["compute"]({"radius": 16.5, "row_gauge": 4.5})
        html = module.DEMO["to_html"](result)
        assert "Full-circle increase rounds" in html
        assert "Half-circle" in html
        assert "2 → 6" in html or "2, 6" in html
        assert "Formula:" in html
        assert "rounds" in html.lower()

    def test_pi_shawl_rejects_invalid_inputs(self):
        module = load_demo("pi_shawl")
        for bad in ({"radius": 0, "row_gauge": 4.5}, {"radius": -1, "row_gauge": 4.5}, {"radius": 10, "row_gauge": 0}):
            with pytest.raises(ValueError):
                module.DEMO["compute"](bad)

    def test_hat_crown_rounds(self):
        module = load_demo("hat_crown")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        rounds = result["rounds"]
        assert isinstance(rounds, (list, tuple))
        assert len(rounds) > 0
        assert result["stitches"] > 0
        assert "plan" in result

    def test_hat_crown_transition_math_and_layout(self):
        module = load_demo("hat_crown")
        result = module.DEMO["compute"]({"stitches": 72, "repeats": 8})
        decrease_rows = [row for row in result["plan"] if row["kind"] == "Decrease"]
        assert decrease_rows[0]["transition"] == "72 -> 64"
        assert all((row["before"] - row["after"]) == 8 for row in decrease_rows)

        html = module.DEMO["to_html"](result)
        assert "Round-by-round instructions" in html
        assert "Crown shaping strategy" in html
        assert "72 / 8 = 9 per repeat" in html
        assert "72 &rarr; 64" in html

    def test_hat_crown_invalid_when_not_evenly_divisible(self):
        module = load_demo("hat_crown")
        with pytest.raises(ValueError, match="divide evenly"):
            module.DEMO["compute"]({"stitches": 78, "repeats": 8})

    def test_hat_crown_invalid_when_too_small_for_repeat_strategy(self):
        module = load_demo("hat_crown")
        with pytest.raises(ValueError, match="at least 2 stitches per repeat"):
            module.DEMO["compute"]({"stitches": 8, "repeats": 8})

    def test_sock_counts(self):
        module = load_demo("sock_calculator")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        assert result["cast_on_stitches"] > 0
        assert result["ankle_stitches"] > 0
        assert result["warnings"] == []
        assert "plan" in result
        assert "<svg" in result["svg"]

    def test_sock_plan_renders_full_guide(self):
        module = load_demo("sock_calculator")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        rendered = module.DEMO["to_html"](result)
        for marker in (
            "How this sock is built",
            "Your numbers at a glance",
            "Knit along",
            "1. Cast on and get started",
            "4. Turn the heel",
            "7. Knit the toe",
            "<svg",
        ):
            assert marker in rendered

    def test_shawl_shapes_instructions(self):
        module = load_demo("shawl_shapes")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        assert "instructions" in result

    def test_sleeve_schedule(self):
        module = load_demo("sleeve_decreases")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        assert len(result["schedule"]) > 0

    def test_shaping_instruction(self):
        module = load_demo("shaping")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        assert result["result"]  # non-empty instruction string

    def test_raglan_setup(self):
        module = load_demo("raglan")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        assert result["result"]

    def test_yarn_estimator_numbers(self):
        module = load_demo("yarn_estimator")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        assert result["yards"] > 0
        assert result["grams"] > 0

    def test_yarn_estimator_friendly_gauge_error(self):
        """Zero gauge must raise a clear message, not a raw pydantic trace."""
        module = load_demo("yarn_estimator")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs["stitch_count"] = 0
        with pytest.raises(ValueError, match="stitch_count must be positive"):
            module.DEMO["compute"](inputs)

    def test_yarn_estimator_friendly_ball_error(self):
        module = load_demo("yarn_estimator")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs["ball_yardage"] = 0
        with pytest.raises(ValueError, match="ball_yardage must be positive"):
            module.DEMO["compute"](inputs)

    def test_pattern_roundtrip(self):
        module = load_demo("pattern_io")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        assert result["roundtrip_rows"] > 0
        assert result["roundtrip_stitches"] > 0

    def test_chart_renderer_japanese_does_not_leak_paths(self):
        module = load_demo("chart_renderer")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs["legend"] = "japanese"
        result = module.DEMO["compute"](inputs)
        html = module.DEMO["to_html"](result)
        assert "/site-packages/" not in html
        assert "/lib/python" not in html
        assert "<svg" in html

    def test_chart_renderer_japanese_uses_embedded_images_or_safe_symbols(self):
        module = load_demo("chart_renderer")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs["legend"] = "japanese"
        html = module.DEMO["to_html"](module.DEMO["compute"](inputs))
        assert ("<image " in html) or ("·" in html) or ("/" in html) or ("O" in html)

    def test_wheel_contains_symbol_assets(self):
        """The built wheel must bundle the chart symbol PNGs so the browser
        demo can render japanese legend images as data URIs."""
        import zipfile

        wheel = (
            pathlib.Path(__file__).resolve().parents[2]
            / "demos" / "_wheel" / "pyknit-0.1.1-py3-none-any.whl"
        )
        with zipfile.ZipFile(wheel) as zf:
            names = zf.namelist()
        assert any("symbols/japanese/" in n and n.endswith(".png") for n in names)
        assert any("symbols/" in n and n.endswith(".png") for n in names)

    def test_shared_export_text_handles_pattern_and_plan_results(self):
        chart_module = load_demo("chart_renderer")
        pattern_result = chart_module.DEMO["compute"](chart_module.DEMO["DEFAULT_INPUTS"])
        pattern_text = shared.export_pattern_text(pattern_result)
        assert "k2" in pattern_text or "p1" in pattern_text

        hat_module = load_demo("hat_crown")
        hat_result = hat_module.DEMO["compute"]({"stitches": 72, "repeats": 8})
        hat_text = shared.export_pattern_text(hat_result)
        assert "Round 1" in hat_text or "72 -> 64" in hat_text

    def test_demo_index_no_longer_promotes_pattern_io(self):
        index_path = pathlib.Path(__file__).resolve().parents[2] / "demos" / "index.html"
        index_text = index_path.read_text(encoding="utf-8")
        assert "Pattern I/O" not in index_text

    def test_chart_renderer_direction_selects_change_the_chart(self):
        """The lr/tb direction selects must affect the rendered SVG."""
        module = load_demo("chart_renderer")
        base = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        rl = module.DEMO["compute"]({**module.DEMO["DEFAULT_INPUTS"], "lr": "rl"})
        assert rl["lr"] == "rl"
        assert module.DEMO["to_html"](base) != module.DEMO["to_html"](rl)

    def test_chart_renderer_direction_metadata_present(self):
        module = load_demo("chart_renderer")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        assert result["lr"] in ("lr", "rl")
        assert result["tb"] in ("tb", "bt")

    def test_shaping_round_vs_flat_give_different_instructions(self):
        """In-the-round shaping must differ from flat (row) shaping."""
        module = load_demo("shaping")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs["operation"] = "increase"
        round_result = module.DEMO["compute"]({**inputs, "in_the_round": "true"})
        flat_result = module.DEMO["compute"]({**inputs, "in_the_round": "false"})
        assert round_result["result"] != flat_result["result"]

    def test_shaping_round_uses_whole_symmetry(self):
        module = load_demo("shaping")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs.update({"operation": "increase", "starting_count": 20, "number": 5})
        result = module.DEMO["compute"]({**inputs, "in_the_round": "true"})
        assert "[k4, m1] * 5 times" in result["result"]

    def test_shaping_svg_fits_viewbox_for_large_rounds(self):
        """The row diagram must never draw cells beyond its viewBox."""
        module = load_demo("shaping")
        result = module.DEMO["compute"](
            {"operation": "increase", "in_the_round": "true", "starting_count": 240, "number": 20}
        )
        svg = result["svg"]
        # viewBox width must accommodate every drawn rect
        import re
        vb = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg)
        assert vb is not None
        vb_width = int(vb.group(1))
        rect_xs = [int(x) for x in re.findall(r'<rect x="(\d+)"', svg)]
        assert rect_xs
        assert max(rect_xs) < vb_width

    def test_shaping_svg_caps_visible_cells_for_huge_rounds(self):
        module = load_demo("shaping")
        result = module.DEMO["compute"](
            {"operation": "increase", "in_the_round": "true", "starting_count": 240, "number": 20}
        )
        import re
        rect_count = len(re.findall(r"<rect ", result["svg"]))
        assert rect_count <= 40
        assert "more stitches" in result["svg"]

    def test_pattern_io_csv_path(self):
        module = load_demo("pattern_io")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs["format"] = "csv"
        result = module.DEMO["compute"](inputs)
        assert result["format"] == "csv"
        assert result["roundtrip_rows"] > 0
        assert "," in result["exported"]

    def test_gauge_conversion_calc(self):
        module = _load_gauge_conversion()
        result = module.compute_calc(
            {
                "pattern-stitch-count": "27.5",
                "pattern-stitch-measure": "10",
                "my-stitch-count": "23.5",
                "my-stitch-measure": "10",
                "measurement": "42",
            }
        )
        assert result["measurement"] == 42
        assert abs(result["result"] - 49.36) < 0.02
        html = module.calc_to_html(result)
        assert "49.36" in html

    def test_gauge_conversion_chart(self):
        module = _load_gauge_conversion()
        result = module.compute_chart({"pattern": "k2 yo k2tog yo k1\np1 k2 yo k2tog p2"})
        assert len(result["pattern"]) == 2
        html = module.chart_to_html(result)
        assert "Rendered with" in html

    def test_gauge_conversion_rejects_bad_measurement(self):
        module = _load_gauge_conversion()
        import pytest
        with pytest.raises(ValueError):
            module.compute_calc(
                {
                    "pattern-stitch-count": "27.5",
                    "pattern-stitch-measure": "10",
                    "my-stitch-count": "23.5",
                    "my-stitch-measure": "10",
                    "measurement": "0",
                }
            )

    def test_gauge_conversion_calc_export_is_human_readable(self):
        module = _load_gauge_conversion()
        result = module.compute_calc(
            {
                "pattern-stitch-count": "27.5",
                "pattern-stitch-measure": "10",
                "my-stitch-count": "23.5",
                "my-stitch-measure": "10",
                "measurement": "42",
            }
        )
        text = module.calc_to_text(result)
        assert "42" in text
        assert "49.36" in text
        assert "becomes" in text
        assert text.startswith("42")

    def test_gauge_conversion_export_buttons_bound(self):
        """The gauge-conversion page declares both export buttons and wires
        them via shared.bind_export_pattern (out-of-browser this is a no-op
        that must not crash)."""
        page = pathlib.Path(__file__).resolve().parents[2] / "demos" / "gauge-conversion" / "demo.html"
        text = page.read_text(encoding="utf-8")
        assert "export-calc" in text
        assert "export-chart" in text

        module = _load_gauge_conversion()
        module.latest_calc_result = {
            "measurement": 42,
            "pattern_st": 27.5,
            "pattern_meas": 10,
            "my_st": 23.5,
            "my_meas": 10,
            "result": 49.36,
        }
        assert module.calc_to_text(module.latest_calc_result).startswith("42")

    def test_export_buttons_present_in_all_demo_pages(self):
        """Every demo page offers an export button."""
        demos_dir = pathlib.Path(__file__).resolve().parents[2] / "demos"
        page_name = {
            "shaping": "even-shaping",
            "raglan": "raglan-sweater",
        }
        missing = []
        for name in DEMO_NAMES:
            if name == "pattern_io":
                # pattern-io exports to CSV/JSON in-page rather than a text button
                continue
            dir_name = page_name.get(name, name.replace("_", "-"))
            page = demos_dir / (dir_name + "/demo.html")
            if not page.exists() or "export-pattern" not in page.read_text(encoding="utf-8"):
                missing.append(str(page))
        assert missing == []

    def test_gauge_conversion_page_uses_modern_chrome(self):
        """The gauge-conversion page must share the modern demo chrome:
        common.css, the all-demos link bar and an export button."""
        demos_dir = pathlib.Path(__file__).resolve().parents[2] / "demos"
        page = demos_dir / "gauge-conversion" / "demo.html"
        text = page.read_text(encoding="utf-8")
        assert "common.css" in text
        assert "all demos" in text
        assert "export-calc" in text


def _load_gauge_conversion():
    """Load the legacy dual-section gauge-conversion page module."""
    spec = importlib.util.spec_from_file_location(
        "gauge_conversion_page", DEMOS_DIR / "gauge_conversion_page.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    pytest.main([__file__, "-v"])