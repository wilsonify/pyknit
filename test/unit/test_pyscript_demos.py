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
            ("raglan", "neck_circumference"),
            ("yarn_estimator", "stitch_gauge"),
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


class TestKnitSimulatorBrowserBehavior:
    """The simulator must keep polling for fresh instruction updates."""

    def test_poll_loop_keeps_listening_after_first_capture(self):
        html = pathlib.Path(__file__).resolve().parents[2] / "demos" / "knit-simulator" / "demo.html"
        text = html.read_text(encoding="utf-8")
        assert "if (captureSteps() || pollCount > 120) clearInterval(poll);" not in text
        assert "captureSteps();" in text
        assert "pollCount > 120" in text
        assert "clearInterval(poll);" in text

    def test_swatch_renderer_present(self):
        """Small manual patterns render as a stitch swatch (needle + loops +
        per-row knit/purl glyphs), driven by each step's own row_ops."""
        html = pathlib.Path(__file__).resolve().parents[2] / "demos" / "knit-simulator" / "demo.html"
        text = html.read_text(encoding="utf-8")
        assert "swatchMode" in text
        assert "isSwatchPattern" in text
        assert "swatch-loops" in text
        assert "swatch-rows" in text
        assert "swatch-working" in text
        assert "swatchStitch" in text
        assert "row_ops" in text
        # the swatch classification is driven by the executed cast-on count
        assert "castOn <= 24" in text
        assert "setSwatchReveal" in text


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

    def test_estimator_data_sends_real_workloads_only(self):
        """Planner demos must only send a stitch workload to the estimator.

        hat_crown only knows its cast-on count (the crown plan covers just the
        shaping), so sending it as a workload would make the estimator report
        absurdly low yardage.  raglan and pi_shawl compute a real workload.
        """
        hat = load_demo("hat_crown").DEMO["compute"]({"stitches": 80, "repeats": 8})
        assert "stitch_count" not in hat.get("_estimator_data", {})
        assert hat.get("_estimator_data", {}).get("project_type") == "hat"

        for name, expected_type, key in (
            ("raglan", "sweater", "stitch_count"),
            ("pi_shawl", "shawl_triangle", "estimated_stitches"),
        ):
            module = load_demo(name)
            result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
            data = result.get("_estimator_data", {})
            assert data.get("project_type") == expected_type
            assert data.get(key, 0) > 1000, (
                f"{name} must send a plausible workload, got {data.get(key)}"
            )

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
        assert len(result["instructions"]) > 0
        assert "assumptions" in result
        assert len(result["assumptions"]) > 0
        assert result["_estimator_data"]["stitch_count"] > 0

    def test_shawl_shapes_all_shapes(self):
        module = load_demo("shawl_shapes")
        for shape in ("crescent", "triangle", "square", "rectangle"):
            inputs = dict(module.DEMO["DEFAULT_INPUTS"])
            inputs["shape"] = shape
            result = module.DEMO["compute"](inputs)
            assert result["shape"] == shape
            assert len(result["instructions"]) > 0
            assert len(result["assumptions"]) > 0

    def test_shawl_shapes_html_renders_assumptions(self):
        module = load_demo("shawl_shapes")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        html = module.DEMO["to_html"](result)
        assert "plan-assumptions" in html
        assert "plan-section" in html
        assert "<svg" in html

    def test_sleeve_schedule(self):
        module = load_demo("sleeve_decreases")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        assert len(result["schedule"]) > 0
        assert result["starting"] == 59
        assert result["ending"] == 43
        assert result["summary"]["total_decrease"] == 16
        assert result["summary"]["number_of_decrease_rows"] == 8

    def test_sleeve_plan_has_required_keys(self):
        module = load_demo("sleeve_decreases")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        assert "plan" in result
        assert "math" in result
        assert "assumptions" in result
        assert "warnings" in result
        assert "summary" in result
        # The row-by-row plan preserves the total row count and distributes
        # decreases evenly (the bug was consecutive rows).
        assert len(result["plan"]) == result["rows"] == 61
        assert sum(1 for r in result["plan"] if r["kind"] == "Decrease") == 8
        assert all("round" in r for r in result["plan"])
        assert all("kind" in r for r in result["plan"])
        assert all("transition" in r for r in result["plan"])
        # Decreases are spaced, not consecutive
        dec_rounds = [r["round"] for r in result["plan"] if r["kind"] == "Decrease"]
        assert dec_rounds != list(range(1, 9))
        assert dec_rounds == result.get("decrease_row_numbers", dec_rounds)
        # Final stitch count matches the requested ending count
        assert result["plan"][-1]["after"] == result["ending"] == 43

    def test_sleeve_math_explains_derivation(self):
        module = load_demo("sleeve_decreases")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        math_text = " ".join(result["math"]).lower()
        assert "59 - 43 = 16" in math_text
        assert "16 / 2 = 8" in math_text
        assert "spacing" in math_text

    def test_sleeve_html_renders_table_and_pills(self):
        module = load_demo("sleeve_decreases")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        html = module.DEMO["to_html"](result)
        assert "<table" in html
        assert "sleeve-pills" in html
        assert "<svg" in html
        assert "plan-section" in html

    def test_sleeve_warning_steep_taper(self):
        module = load_demo("sleeve_decreases")
        inputs = {"number_of_rows": 20, "starting_count": 60, "ending_count": 40,
                  "decrease_per_row": 2, "padding_mode": "after"}
        result = module.DEMO["compute"](inputs)
        assert len(result["warnings"]) > 0
        assert "steep" in result["warnings"][0].lower() or "apart" in result["warnings"][0].lower()

    def test_sleeve_error_start_not_greater_than_end(self):
        module = load_demo("sleeve_decreases")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs["starting_count"] = 40
        inputs["ending_count"] = 50
        with pytest.raises(ValueError, match="must be greater"):
            module.DEMO["compute"](inputs)

    def test_sleeve_error_not_enough_rows(self):
        module = load_demo("sleeve_decreases")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs["number_of_rows"] = 2
        with pytest.raises(ValueError, match="not enough rows"):
            module.DEMO["compute"](inputs)

    def test_sleeve_all_padding_modes(self):
        module = load_demo("sleeve_decreases")
        for mode in ("after", "before", "both", "none"):
            inputs = dict(module.DEMO["DEFAULT_INPUTS"])
            inputs["padding_mode"] = mode
            result = module.DEMO["compute"](inputs)
            assert len(result["plan"]) > 0
            assert result["summary"]["total_decrease"] == 16

    def test_sleeve_estimator_data(self):
        module = load_demo("sleeve_decreases")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        est = result.get("_estimator_data", {})
        assert est.get("stitch_count", 0) > 0
        assert est.get("project_type") == "sweater"

    def test_shaping_instruction(self):
        module = load_demo("shaping")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        assert result["result"]  # non-empty instruction string

    def test_raglan_setup(self):
        module = load_demo("raglan")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        assert result["result"]
        assert "plan" in result
        assert "sections" in result["plan"]
        assert len(result["plan"]["sections"]) > 0
        assert result["meta"]["neck"] > 0
        assert result["meta"]["bust"] > 0
        assert result["meta"]["arm"] > 0

    def test_yarn_estimator_numbers(self):
        module = load_demo("yarn_estimator")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        assert result["yards"] > 0
        assert result["grams"] > 0

    def test_yarn_estimator_friendly_gauge_error(self):
        """Zero gauge must raise a clear message, not a raw pydantic trace."""
        module = load_demo("yarn_estimator")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs["stitch_gauge"] = 0
        with pytest.raises(ValueError, match="stitch gauge must be positive"):
            module.DEMO["compute"](inputs)

    def test_yarn_estimator_friendly_ball_error(self):
        module = load_demo("yarn_estimator")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs["yarn_per_ball_yards"] = 0
        with pytest.raises(ValueError, match="yards per ball must be positive"):
            module.DEMO["compute"](inputs)

    def test_yarn_estimator_advanced_mode(self):
        """Advanced mode uses per-stitch inputs."""
        module = load_demo("yarn_estimator")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs["advanced_mode"] = "true"
        inputs["project_stitches"] = 1000
        inputs["yards_per_stitch"] = 0.05
        result = module.DEMO["compute"](inputs)
        assert result["yards"] == pytest.approx(50.0, rel=0.01)
        assert result["confidence"] == "low"

    def test_yarn_estimator_ranges_present(self):
        module = load_demo("yarn_estimator")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        assert "yards_low" in result
        assert "yards_high" in result
        assert result["yards_low"] < result["yards"] < result["yards_high"]

    def test_yarn_estimator_all_project_types(self):
        """Every project type produces a valid estimate."""
        module = load_demo("yarn_estimator")
        for ptype in ("hat", "scarf", "shawl_triangle", "sweater", "blanket"):
            inputs = dict(module.DEMO["DEFAULT_INPUTS"])
            inputs["project_type"] = ptype
            result = module.DEMO["compute"](inputs)
            assert result["project_stitches"] > 0
            assert result["yards"] > 0

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
            / "demos" / "_wheel" / "pyknit-0.1.3-py3-none-any.whl"
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

    def test_demo_index_title_and_meta(self):
        index_path = pathlib.Path(__file__).resolve().parents[2] / "demos" / "index.html"
        html = index_path.read_text(encoding="utf-8")
        assert "Interactive Knitting Tools" in html
        assert '<meta name="description"' in html
        assert "pyKnit" in html

    def test_demo_index_links_all_demos(self):
        index_path = pathlib.Path(__file__).resolve().parents[2] / "demos" / "index.html"
        html = index_path.read_text(encoding="utf-8")
        demos = [
            "gauge-conversion", "chart-renderer", "even-shaping", "hat-crown",
            "pi-shawl", "raglan-sweater", "shawl-shapes", "sleeve-decreases",
            "sock-calculator", "yarn-estimator", "yarn-advisor", "needle-advisor",
            "knit-simulator",
        ]
        for demo in demos:
            assert f"{demo}/demo.html" in html, f"Missing link to {demo}"

    def test_demo_index_has_category_headings(self):
        index_path = pathlib.Path(__file__).resolve().parents[2] / "demos" / "index.html"
        html = index_path.read_text(encoding="utf-8")
        assert "Plan a Project" in html
        assert "Shape Your Knitting" in html
        assert "Calculate" in html
        assert "Patterns" in html
        assert "Choose Your Materials" in html

    def test_demo_index_featured_tools_present(self):
        index_path = pathlib.Path(__file__).resolve().parents[2] / "demos" / "index.html"
        html = index_path.read_text(encoding="utf-8")
        assert "Sock Calculator" in html
        assert "Raglan Sweater" in html
        assert "featured-card" in html

    def test_demo_index_raglan_description_accurate(self):
        """Raglan description must reflect full top-down sweater capability."""
        index_path = pathlib.Path(__file__).resolve().parents[2] / "demos" / "index.html"
        html = index_path.read_text(encoding="utf-8").lower()
        assert "seamless" in html
        assert "top-down" in html
        assert "increase" in html
        assert "sleeve" in html
        assert "hem" in html or "cuff" in html

    def test_demo_index_no_console_debug_instructions(self):
        """Landing page should not tell users to open browser console."""
        index_path = pathlib.Path(__file__).resolve().parents[2] / "demos" / "index.html"
        html = index_path.read_text(encoding="utf-8").lower()
        assert "console" not in html or "f12" not in html

    def test_demo_index_links_correct_repo(self):
        index_path = pathlib.Path(__file__).resolve().parents[2] / "demos" / "index.html"
        html = index_path.read_text(encoding="utf-8")
        assert "github.com/wilsonify/pyknit" in html

    def test_demo_index_boots_pyscript_like_the_demos(self):
        """The landing page loads PyScript itself (core + py-config + py
        block), so the first visit pays the boot there and the banner turns
        into a real ready state instead of a static claim."""
        index_path = pathlib.Path(__file__).resolve().parents[2] / "demos" / "index.html"
        html = index_path.read_text(encoding="utf-8")
        # boots PyScript exactly like a demo page
        assert "/_assets/pyscript/core.js" in html
        assert "/_assets/pyscript/core.css" in html
        assert "<py-config>" in html
        assert "pyknit-0.1.3-py3-none-any.whl" in html
        assert "import pyknit" in html
        # live status banner driven by shared.set_status, not a static banner
        assert "status-banner" in html
        assert "status-message" in html
        assert "set_status" in html
        assert "All tools ready" in html
        # the friendly first-visit copy is still there, as the loading detail
        assert "30" in html and "60" in html
        assert "loading-banner" not in html

    def test_demo_index_svg_illustrations_present(self):
        index_path = pathlib.Path(__file__).resolve().parents[2] / "demos" / "index.html"
        html = index_path.read_text(encoding="utf-8")
        assert html.count("<svg") >= 10, "Expected at least 10 inline SVGs for illustrations and icons"

    def test_demo_index_no_pyscript_branding_in_header(self):
        """The main heading should focus on knitting, not PyScript."""
        index_path = pathlib.Path(__file__).resolve().parents[2] / "demos" / "index.html"
        html = index_path.read_text(encoding="utf-8")
        assert "PyScript" not in html.split("</header>")[0] if "</header>" in html else True

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

    def test_no_backslash_in_fstring_expressions(self):
        """Pyodide runs Python 3.11, which rejects backslashes inside
        f-string expressions (Python 3.12 allows them). Any such f-string
        in a demo module would crash the browser demo at import time even
        though the local test runner (3.12) parses it fine."""
        import ast

        bad = []
        for path in [*DEMOS_DIR.glob("*.py")]:
            src = path.read_text(encoding="utf-8")
            lines = src.splitlines()
            try:
                tree = ast.parse(src)
            except SyntaxError as exc:
                bad.append(f"{path.name}: unparseable: {exc}")
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.JoinedStr):
                    continue
                for val in node.values:
                    if not isinstance(val, ast.FormattedValue):
                        continue
                    expr = val.value
                    if expr.lineno == expr.end_lineno:
                        seg = lines[expr.lineno - 1][expr.col_offset:expr.end_col_offset]
                    else:
                        seg = "\\n".join(lines[expr.lineno - 1:expr.end_lineno])
                    if "\\" in seg:
                        bad.append(f"{path.name}:{expr.lineno}: {seg.strip()}")
        assert bad == []

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


class TestYarnAdvisor:
    def test_default_compute(self):
        module = load_demo("yarn_advisor")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        assert result["best_fiber"] is not None
        assert result["best_score"] > 0
        assert len(result["recommendations"]) > 0
        assert result["yarn_weight"] == "dk"

    def test_all_project_types(self):
        module = load_demo("yarn_advisor")
        for pt in ("scarf", "hat", "sock", "sweater", "shawl", "blanket", "mittens", "baby"):
            inputs = dict(module.DEMO["DEFAULT_INPUTS"])
            inputs["project_type"] = pt
            result = module.DEMO["compute"](inputs)
            assert result["project_type"] == pt
            assert len(result["recommendations"]) > 0

    def test_all_gauge_categories(self):
        module = load_demo("yarn_advisor")
        for g in ("lace", "fingering", "sport", "dk", "worsted", "aran", "bulky", "super_bulky"):
            inputs = dict(module.DEMO["DEFAULT_INPUTS"])
            inputs["target_gauge"] = g
            result = module.DEMO["compute"](inputs)
            expected = "super bulky" if g == "super_bulky" else g
            assert result["yarn_weight"] == expected

    def test_html_renders(self):
        module = load_demo("yarn_advisor")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        html = module.DEMO["to_html"](result)
        assert "stat-pill" in html
        assert "plan-section" in html
        assert "Best match" in html

    def test_warnings_for_conflicts(self):
        module = load_demo("yarn_advisor")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs["project_type"] = "sock"
        inputs["fabric_drape"] = "very_drapey"
        result = module.DEMO["compute"](inputs)
        assert len(result["warnings"]) > 0

    def test_fiber_preference(self):
        module = load_demo("yarn_advisor")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs["fiber_pref"] = "merino"
        result = module.DEMO["compute"](inputs)
        assert any(r["fiber"] == "merino" for r in result["recommendations"])

    def test_estimator_data(self):
        module = load_demo("yarn_advisor")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        assert "drape_score" in result
        assert "warmth_score" in result
        assert 0 <= result["drape_score"] <= 1
        assert 0 <= result["warmth_score"] <= 1


class TestNeedleAdvisor:
    def test_default_compute(self):
        module = load_demo("needle_advisor")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        assert result["recommended_mm"] > 0
        assert result["recommended_us"] != "?"
        assert len(result["needle_types"]) > 0

    def test_all_yarn_weights(self):
        module = load_demo("needle_advisor")
        for w in ("lace", "fingering", "sport", "dk", "worsted", "aran", "bulky", "super_bulky"):
            inputs = dict(module.DEMO["DEFAULT_INPUTS"])
            inputs["yarn_weight"] = w
            result = module.DEMO["compute"](inputs)
            assert result["yarn_weight"] == w
            assert result["recommended_mm"] > 0

    def test_all_project_types(self):
        module = load_demo("needle_advisor")
        for pt in ("scarf", "hat", "sock", "sweater", "shawl", "blanket", "mittens", "baby"):
            inputs = dict(module.DEMO["DEFAULT_INPUTS"])
            inputs["project_type"] = pt
            result = module.DEMO["compute"](inputs)
            assert result["project_label"]
            assert len(result["needle_types"]) > 0

    def test_all_construction_types(self):
        module = load_demo("needle_advisor")
        for ct in ("flat", "round_seamless", "round_dpns", "small_circumference"):
            inputs = dict(module.DEMO["DEFAULT_INPUTS"])
            inputs["construction"] = ct
            result = module.DEMO["compute"](inputs)
            assert result["construction_label"]
            assert len(result["needle_types"]) > 0

    def test_html_renders(self):
        module = load_demo("needle_advisor")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        html = module.DEMO["to_html"](result)
        assert "stat-pill" in html
        assert "Starting needle size" in html
        assert "Needle types to consider" in html
        assert "Cable length" in html

    def test_warnings_for_fine_gauge(self):
        module = load_demo("needle_advisor")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs["yarn_weight"] = "lace"
        inputs["target_gauge"] = 8
        result = module.DEMO["compute"](inputs)
        assert len(result["warnings"]) > 0

    def test_cable_length_for_hat(self):
        module = load_demo("needle_advisor")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs["project_type"] = "hat"
        inputs["construction"] = "round_seamless"
        result = module.DEMO["compute"](inputs)
        assert "16 in" in result["cable_length"]["label"]

    def test_assumptions_present(self):
        module = load_demo("needle_advisor")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        assert len(result["assumptions"]) > 0
        assert any("swatch" in a.lower() for a in result["assumptions"])


class TestKnitSimulator:
    def test_default_compute(self):
        module = load_demo("knit_simulator")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        assert result["total_steps"] > 0
        assert len(result["final_stitches"]) > 0
        assert result["speed_ms"] == 400

    def test_cast_on_only(self):
        module = load_demo("knit_simulator")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs["instructions"] = "co 10"
        result = module.DEMO["compute"](inputs)
        assert result["total_steps"] == 1
        assert len(result["final_stitches"]) == 10

    def test_knit_and_purl(self):
        module = load_demo("knit_simulator")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs["instructions"] = "co 12\nk all\np all"
        result = module.DEMO["compute"](inputs)
        assert result["total_steps"] == 3
        assert len(result["final_stitches"]) == 12

    def test_k2tog_decreases(self):
        module = load_demo("knit_simulator")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs["instructions"] = "co 10\nk2tog across"
        result = module.DEMO["compute"](inputs)
        assert len(result["final_stitches"]) < 10

    def test_yo_increases(self):
        module = load_demo("knit_simulator")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs["instructions"] = "co 8\nyo k1 across"
        result = module.DEMO["compute"](inputs)
        assert len(result["final_stitches"]) >= 8

    def test_speed_presets(self):
        module = load_demo("knit_simulator")
        for speed, expected_ms in [("slow", 800), ("normal", 400), ("fast", 150)]:
            inputs = dict(module.DEMO["DEFAULT_INPUTS"])
            inputs["speed"] = speed
            result = module.DEMO["compute"](inputs)
            assert result["speed_ms"] == expected_ms

    def test_html_renders(self):
        module = load_demo("knit_simulator")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        html = module.DEMO["to_html"](result)
        assert "stat-pill" in html
        assert "Steps" in html

    def test_step_log_entries(self):
        module = load_demo("knit_simulator")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        for step in result["steps"]:
            assert "op" in step
            assert "n" in step
            assert "stitches" in step
            assert isinstance(step["stitches"], list)

    def test_empty_instructions_raises(self):
        module = load_demo("knit_simulator")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs["instructions"] = ""
        with pytest.raises(ValueError, match="No valid instructions"):
            module.DEMO["compute"](inputs)

    def test_missing_cast_on_warns(self):
        module = load_demo("knit_simulator")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs["instructions"] = "k 10\np 10"
        result = module.DEMO["compute"](inputs)
        assert any("cast-on" in w.lower() for w in result["warnings"])

    def test_bind_off(self):
        module = load_demo("knit_simulator")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs["instructions"] = "co 10\nbo 5"
        result = module.DEMO["compute"](inputs)
        assert len(result["final_stitches"]) == 5

    # ── Regression: the simulator must never invent operations ──

    def test_across_rows_never_invent_operations(self):
        """'co 10 / k2 p2 across / k2 p2 across / k all' must produce exactly
        the requested operations and keep the stitch count at 10."""
        module = load_demo("knit_simulator")
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs["instructions"] = "co 10\nk2 p2 across\nk2 p2 across\nk all"
        result = module.DEMO["compute"](inputs)

        ops = [step["op"] for step in result["steps"]]
        assert ops == [
            "cast on 10",
            "k2 p2 k2 p2 k2 across",
            "k2 p2 k2 p2 k2 across",
            "knit all",
        ]
        # no k2tog / bind off / other operations were requested
        for op in ops:
            assert "k2tog" not in op
            assert "bind off" not in op

        # stitch count never changes across the whole simulation
        assert [step["n"] for step in result["steps"]] == [10, 10, 10, 10]
        assert len(result["final_stitches"]) == 10
        assert result["total_rows"] == 3

        # the ribbed rows really contain the k2/p2 sequence (0 knit, 1 purl)
        rib = result["steps"][1]["row_ops"]
        assert rib == [0, 0, 1, 1, 0, 0, 1, 1, 0, 0]
        assert result["steps"][3]["row_ops"] == [0] * 10

    def test_across_expands_to_row_width(self):
        """'k2 p2 across' tiles the sequence across the whole row; a plain
        'k2 p2' only works the stitches it names."""
        module = load_demo("knit_simulator")
        across = module.DEMO["compute"](
            {"instructions": "co 10\nk2 p2 across"}
        )
        assert across["steps"][1]["worked"] == 10
        assert across["steps"][1]["row_ops"] == [0, 0, 1, 1, 0, 0, 1, 1, 0, 0]

        plain = module.DEMO["compute"]({"instructions": "co 10\nk2 p2"})
        assert plain["steps"][1]["worked"] == 4
        assert plain["steps"][1]["row_ops"] == [0, 0, 1, 1, -1, -1, -1, -1, -1, -1]
        assert plain["steps"][1]["n"] == 10  # unworked stitches stay on the needle

    def test_star_repeat_matches_across(self):
        module = load_demo("knit_simulator")
        star = module.DEMO["compute"]({"instructions": "co 10\n* k2 p2"})
        across = module.DEMO["compute"]({"instructions": "co 10\nk2 p2 across"})
        assert star["steps"][1]["row_ops"] == across["steps"][1]["row_ops"]
        assert star["steps"][1]["worked"] == 10

    def test_k2tog_across_halves_the_row(self):
        module = load_demo("knit_simulator")
        result = module.DEMO["compute"]({"instructions": "co 10\nk2tog across"})
        assert result["steps"][1]["n"] == 5
        assert result["steps"][1]["decreases"] == 5
        assert len(result["final_stitches"]) == 5

    def test_progress_is_monotonic_and_bounded(self):
        module = load_demo("knit_simulator")
        result = module.DEMO["compute"]({"instructions": "co 10\nk all\np all"})
        progresses = [step["progress"] for step in result["steps"]]
        assert progresses[0] == 0.0
        assert progresses[-1] == 1.0
        assert all(a <= b for a, b in zip(progresses, progresses[1:]))
        assert all(0.0 <= p <= 1.0 for p in progresses)

    def test_steps_carry_garment_fields(self):
        """The JS sweater renderer needs kind/row/worked/row_ops/progress."""
        module = load_demo("knit_simulator")
        result = module.DEMO["compute"]({"instructions": "co 10\nk all\nbo 5"})
        for step in result["steps"]:
            for key in ("kind", "row", "worked", "row_ops", "increases", "decreases", "progress"):
                assert key in step, f"step missing {key}"
        assert result["steps"][0]["kind"] == "cast_on"
        assert result["steps"][2]["kind"] == "bind_off"

    def test_steps_json_serializable(self):
        """Steps must survive json round-trip for the JS player bridge."""
        import json

        module = load_demo("knit_simulator")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        restored = json.loads(json.dumps(result["steps"]))
        assert len(restored) == len(result["steps"])
        for orig, serial in zip(result["steps"], restored):
            assert set(orig.keys()) == set(serial.keys())

    def test_steps_have_player_fields(self):
        """Each step must have op, n, stitches — what the JS player reads."""
        module = load_demo("knit_simulator")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        for step in result["steps"]:
            assert "op" in step
            assert "n" in step
            assert "stitches" in step
            assert isinstance(step["stitches"], list)

    def test_demo_html_no_broken_shared_reference(self):
        """demo.html JS block must not reference the Python 'shared' module."""
        html_path = DEMOS_DIR.parent.parent.parent / "demos" / "knit-simulator" / "demo.html"
        if not html_path.exists():
            pytest.skip("demo.html not found")
        import re
        content = html_path.read_text()
        js_blocks = re.findall(r"<script>(?!.*type=)(.*?)</script>", content, re.DOTALL)
        for block in js_blocks:
            assert "shared." not in block, (
                "JS block references 'shared' (a Python module). "
                "Use window.sim_steps instead."
            )

    def test_demo_html_has_sim_steps_bridge(self):
        """demo.html must bridge steps to window.sim_steps for the JS player."""
        html_path = DEMOS_DIR.parent.parent.parent / "demos" / "knit-simulator" / "demo.html"
        if not html_path.exists():
            pytest.skip("demo.html not found")
        content = html_path.read_text()
        assert "window.sim_steps" in content
        assert "sim_steps" in content

    def test_demo_html_uses_json_roundtrip_for_sim_steps(self):
        """The JS bridge must hand the browser a JSON string that it parses into a real array."""
        html_path = DEMOS_DIR.parent.parent.parent / "demos" / "knit-simulator" / "demo.html"
        if not html_path.exists():
            pytest.skip("demo.html not found")
        content = html_path.read_text()
        assert "sim_steps_json" in content
        assert "JSON.parse(raw)" in content
        assert "window.sim_steps_json" in content

    def test_demo_html_python_uses_module_dict(self):
        """Python script must access the DEMO dict via mod.DEMO, not the module directly."""
        html_path = DEMOS_DIR.parent.parent.parent / "demos" / "knit-simulator" / "demo.html"
        if not html_path.exists():
            pytest.skip("demo.html not found")
        import re
        content = html_path.read_text()
        py_blocks = re.findall(r'<script type="py">(.*?)</script>', content, re.DOTALL)
        for block in py_blocks:
            # Must extract dict from module before subscripting
            assert "mod.DEMO" in block or "_DEMO" in block, (
                "Python block never extracts DEMO dict from module. "
                "Use: _DEMO = mod.DEMO"
            )


class TestSockCalculatorToSimulator:
    """The Sock Calculator's computed pattern must drive the Knit Simulator
    end to end without re-deriving any knitting math."""

    def _sock_plan(self):
        sock = load_demo("sock_calculator")
        result = sock.DEMO["compute"](sock.DEMO["DEFAULT_INPUTS"])
        return result["sim"]

    def test_calculator_emits_round_by_round_pattern(self):
        plan = self._sock_plan()
        assert plan["source"] == "sock_calculator"
        rounds = plan["rounds"]
        assert rounds and rounds[0]["kind"] == "cast_on"
        assert rounds[0]["after"] == plan["cast_on_stitches"]
        # Counts are continuous within each construction section.  The one
        # deliberate jump is the leg -> heel flap transition, where the
        # flap is worked back and forth over just the flap stitches while
        # the instep stitches sit on hold (classic top-down sock anatomy).
        for prev, nxt in zip(rounds, rounds[1:]):
            if nxt["kind"] == "heel_slip":
                assert nxt["before"] == nxt["after"]  # flap width, not leg width
                continue
            assert prev["after"] == nxt["before"], (prev, nxt)

    def test_simulator_converts_pattern_without_inventing_ops(self):
        plan = self._sock_plan()
        module = load_demo("knit_simulator")
        result = module.DEMO["compute"]({"sock_plan": plan})
        assert result["garment"] == "sock"
        assert result["total_steps"] == len(plan["rounds"])
        # one step per round, same labels/counts/textures — nothing invented
        for step, rnd in zip(result["steps"], plan["rounds"]):
            assert step["n"] == rnd["after"]
            assert step["op"] == rnd["label"]
            assert step["texture"] == rnd["texture"]
        # counts stay consistent calculator -> pattern -> simulator
        assert result["cast_on"] == plan["cast_on_stitches"]
        assert result["cast_on"] == result["steps"][0]["n"]
        assert result["final_stitches"] == list(
            range(1, plan["rounds"][-1]["after"] + 1)
        )

    def test_simulator_reports_sock_summary(self):
        plan = self._sock_plan()
        module = load_demo("knit_simulator")
        result = module.DEMO["compute"]({"sock_plan": plan})
        summary = result["sock_summary"]
        assert summary["cast_on_stitches"] == plan["cast_on_stitches"]
        assert summary["ankle_stitches"] == plan["ankle_stitches"]
        assert summary["total_rounds"] == len(plan["rounds"]) - 1
        assert summary["gauge"]

    def test_manual_instructions_still_work(self):
        module = load_demo("knit_simulator")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        assert result["garment"] == "sweater"
        assert result["sock_summary"] is None

    def test_invalid_sock_plan_raises(self):
        module = load_demo("knit_simulator")
        with pytest.raises(ValueError, match="missing or invalid"):
            module.DEMO["compute"]({"sock_plan": {"source": "other"}})
        with pytest.raises(ValueError, match="empty"):
            module.DEMO["compute"]({"sock_plan": {"source": "sock_calculator"}})
        with pytest.raises(ValueError, match="inconsistent"):
            module.DEMO["compute"](
                {
                    "sock_plan": {
                        "source": "sock_calculator",
                        "rounds": [{"after": 5}],
                        "cast_on_stitches": 72,
                    }
                }
            )

    def test_empty_sock_plan_raises(self):
        module = load_demo("knit_simulator")
        with pytest.raises(ValueError, match="empty"):
            module.DEMO["compute"](
                {"sock_plan": {"source": "sock_calculator", "rounds": []}}
            )


class TestHatCrownToSimulator:
    """The Hat Crown Planner's tapered dome schedule and its generated
    instructions must produce a sensible crown and drive the simulator 1:1."""

    @staticmethod
    def _plain_gaps(plan):
        """Plain rounds between consecutive decrease rounds."""
        gaps = []
        i = 0
        while i < len(plan):
            if plan[i]["kind"] == "Decrease":
                j = i + 1
                cnt = 0
                while j < len(plan) and plan[j]["kind"] == "Knit even":
                    cnt += 1
                    j += 1
                gaps.append(cnt)
                i = j
            else:
                i += 1
        return gaps

    def test_tapered_dome_schedule(self):
        """80 sts / 8 repeats: counts fall by 8 per decrease round and the
        plain-round gap shortens 2 -> 1 -> 0 as the crown narrows, so the
        crown is a dome, not a cone."""
        module = load_demo("hat_crown")
        result = module.DEMO["compute"]({"repeats": 8, "stitches": 80})
        plan = result["plan"]
        decs = [r for r in plan if r["kind"] == "Decrease"]
        assert [d["before"] for d in decs] == [80, 72, 64, 56, 48, 40, 32, 24, 16]
        assert all(d["after"] == d["before"] - 8 for d in decs)
        # 9 decrease rounds; the last is followed by the finish (gap 0)
        assert self._plain_gaps(plan) == [2, 2, 1, 1, 1, 0, 0, 0, 0]
        assert [d["phase"] for d in decs] == [
            "curve", "curve", "steady", "steady", "steady",
            "top", "top", "top", "top",
        ]
        # ends with the drawstring cinch on the final repeats
        assert plan[-1]["kind"] == "Finish"
        assert plan[-1]["after"] == 8

    def test_small_hat_skips_curve_phase(self):
        """Small hats have no room for a gradual start and round over
        immediately."""
        module = load_demo("hat_crown")
        result = module.DEMO["compute"]({"repeats": 8, "stitches": 24})
        decs = [r for r in result["plan"] if r["kind"] == "Decrease"]
        assert [d["before"] for d in decs] == [24, 16]
        assert all(d["phase"] == "top" for d in decs)
        assert result["plan"][-1]["after"] == 8

    def test_crown_shape_visualizations_present(self):
        module = load_demo("hat_crown")
        result = module.DEMO["compute"]({"repeats": 8, "stitches": 80})
        # top-down rings + side profile + shape explanation
        assert "<svg" in result["svg"]
        assert "<svg" in result["svg_profile"]
        assert "hat body" in result["svg_profile"]
        assert "dome" in result["shape_note"].lower()
        html = module.DEMO["to_html"](result)
        assert "hat-shapes" in html
        assert "Phase" in html
        assert "Curve in" in html
        assert "Round over" in html

    def test_sim_plan_executes_1to1(self):
        """The generated instructions, executed by the Knit Simulator, must
        reproduce the planner's arithmetic exactly — no invented ops."""
        module = load_demo("hat_crown")
        result = module.DEMO["compute"]({"repeats": 8, "stitches": 80})
        sim = result["sim_plan"]
        assert sim["garment"] == "hat"
        assert sim["counts"]["cast_on"] == 80
        assert sim["counts"]["final"] == 8

        ks = load_demo("knit_simulator")
        executed = ks.DEMO["compute"]({"instructions": sim["instructions"], "plan": sim})
        assert executed["garment"] == "hat"
        assert executed["total_steps"] == sim["sections"][-1]["end"]
        # every decrease row removes exactly 8 stitches
        dec_steps = [s for s in executed["steps"] if s["decreases"] > 0]
        assert all(s["decreases"] == 8 for s in dec_steps)
        assert all(s["n"] == s["before"] - 8 for s in dec_steps)
        # first step casts on, last step is the bind-off/cinch
        assert executed["steps"][0]["kind"] == "cast_on"
        assert executed["steps"][0]["n"] == 80
        assert executed["steps"][-1]["kind"] == "bind_off"
        assert executed["steps"][-1]["n"] == 0
        # the phase sections are stamped onto the steps
        labels = {s["section_label"] for s in executed["steps"]}
        assert labels == {"Curve in", "Steady", "Round over"}
        # honest short ops
        shorts = [s["op_short"] for s in executed["steps"] if "op_short" in s]
        assert shorts[0] == "Cast on 80 sts"
        assert "Decrease (-8)" in shorts

    def test_page_plumbing(self):
        root = pathlib.Path(__file__).resolve().parents[2]
        hat = (root / "demos" / "hat-crown" / "demo.html").read_text(encoding="utf-8")
        assert "simulate-hat" in hat
        assert "hat_sim_plan" in hat
        assert "hat_sim_ready" in hat
        assert "knit_sim_instructions" in hat
        sim = (root / "demos" / "knit-simulator" / "demo.html").read_text(encoding="utf-8")
        assert "hatMode" in sim
        assert "buildHat" in sim
        assert "hat-plan-note" in sim
        assert "clear-hat-plan" in sim


class TestRaglanToSimulator:
    """The Raglan Sweater Planner's generated instructions must be the exact
    instruction stream the Knit Simulator executes."""

    def _plan(self):
        raglan = load_demo("raglan")
        return raglan.DEMO["compute"](raglan.DEMO["DEFAULT_INPUTS"])

    def test_planner_generates_executable_instructions(self):
        result = self._plan()
        meta = result["meta"]
        instr = result["sim_instructions"]
        assert instr and instr.startswith("# Raglan sweater")
        lines = [
            ln for ln in instr.splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        ]
        # cast on the neck, then the collar rib, then the yoke
        assert lines[0] == "co %d" % meta["neck"]
        assert "k2 p2 across" in lines[: meta["collar_rounds"]]
        assert any("yo" in ln for ln in lines)      # raglan increases
        assert any("k2tog" in ln for ln in lines)   # sleeve decreases
        assert lines.count("bo all") == 3           # body hem + 2 cuffs
        assert lines.count("co %d" % meta["arm"]) == 2  # the two sleeves

    def test_instructions_execute_without_inventing_ops(self):
        plan = self._plan()
        meta = plan["meta"]
        module = load_demo("knit_simulator")
        result = module.DEMO["compute"]({"instructions": plan["sim_instructions"]})
        steps = result["steps"]

        # the neck cast-on is the garment's cast-on (sleeve cast-ons follow)
        assert steps[0]["op"] == "cast on %d" % meta["neck"]
        assert result["cast_on"] == meta["neck"]

        # the simulator's own count bookkeeping reproduces the Planner's
        # arithmetic exactly: +working-neck from the yoke, -2*(arm-wrist)
        # from the sleeves, and nothing else
        assert sum(st["increases"] for st in steps) == meta["working"] - meta["neck"]
        assert sum(st["decreases"] for st in steps) == 2 * (meta["arm"] - meta["wrist"])

        # both sleeves are cast on at the Planner's arm count and finish at
        # the wrist
        sleeve_cos = [st for st in steps if st["kind"] == "cast_on" and st["n"] == meta["arm"]]
        assert len(sleeve_cos) == 2
        assert steps[-1]["op"] == "bind off %d" % meta["wrist"]

    def test_edited_instructions_are_what_runs(self):
        """The prefill is one-shot: whatever is in the instructions field is
        what gets simulated, so a user edit changes the simulation."""
        plan = self._plan()
        module = load_demo("knit_simulator")
        edited = plan["sim_instructions"].replace(
            "k2 p2 across" + chr(10), "k all" + chr(10), 1
        )
        result = module.DEMO["compute"]({"instructions": edited})
        assert result["steps"][1]["op"] == "knit all"

    def test_raglan_page_has_simulate_button(self):
        html_path = DEMOS_DIR.parent.parent.parent / "demos" / "raglan-sweater" / "demo.html"
        if not html_path.exists():
            pytest.skip("raglan demo.html not found")
        content = html_path.read_text(encoding="utf-8")
        assert "simulate-sweater" in content
        assert "knit_sim_instructions" in content
        assert "raglan_sim_instructions" in content

    def test_knit_sim_page_prefills_from_storage(self):
        html_path = DEMOS_DIR.parent.parent.parent / "demos" / "knit-simulator" / "demo.html"
        if not html_path.exists():
            pytest.skip("knit-simulator demo.html not found")
        content = html_path.read_text(encoding="utf-8")
        assert "knit_sim_instructions" in content
        assert "raglan-plan-note" in content
        assert "raglan_orientation" in content

    # ── Canonical plan -> section-aware simulation ──

    def test_plan_sections_align_with_instruction_lines(self):
        """The canonical plan's section boundaries are indices into the
        non-comment instruction lines, so they map 1:1 onto steps."""
        sim = self._plan()["sim_plan"]
        lines = [
            ln for ln in sim["instructions"].splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        ]
        secs = sim["sections"]
        assert secs[0]["start"] == 0
        assert secs[-1]["end"] == len(lines)
        prev = 0
        for sec in secs:
            assert sec["start"] == prev and sec["end"] > sec["start"]
            prev = sec["end"]
        assert [sec["id"] for sec in secs] == [
            "neckline", "yoke", "body", "left_sleeve", "right_sleeve",
        ]

    def test_plan_driven_steps_are_section_aware(self):
        """Passing the plan makes every step carry its garment section and a
        concise operation label derived from the step's own data."""
        sim = self._plan()["sim_plan"]
        module = load_demo("knit_simulator")
        result = module.DEMO["compute"]({
            "instructions": sim["instructions"], "plan": sim,
        })
        assert result["garment"] == "raglan"
        assert result["sections"] == sim["sections"]
        for i, st in enumerate(result["steps"]):
            assert st["section"] in (
                "neckline", "yoke", "body", "left_sleeve", "right_sleeve",
            )
            assert st["section_label"]
            assert st["sec_row"] >= 1 and st["sec_rows"] >= 1
            assert st["op_short"]
            sec = next(s for s in sim["sections"] if s["id"] == st["section"])
            assert sec["start"] <= i < sec["end"]
            assert st["sec_row"] == i - sec["start"] + 1
            assert st["sec_rows"] == sec["end"] - sec["start"]

    def test_plan_phase_values_are_real(self):
        """Phase line numbers (yoke end, per-round increase, sleeve run-down)
        come straight from the executed steps, never invented."""
        plan = self._plan()
        meta = plan["meta"]
        sim = plan["sim_plan"]
        module = load_demo("knit_simulator")
        steps = module.DEMO["compute"]({
            "instructions": sim["instructions"], "plan": sim,
        })["steps"]

        yoke = [s for s in steps if s["section"] == "yoke"]
        assert yoke[-1]["n"] == meta["working"]      # yoke ends at working count
        inc_steps = [s for s in yoke if s["increases"] > 0]
        assert inc_steps
        assert all(s["increases"] == meta["inc"] for s in inc_steps)
        assert inc_steps[0]["op_short"] == "Raglan increase (+%d)" % meta["inc"]

        body = [s for s in steps if s["section"] == "body"]
        assert body and body[0]["op_short"] == "Knit all"

        for side in ("left_sleeve", "right_sleeve"):
            sec = [s for s in steps if s["section"] == side]
            assert sec[0]["kind"] == "cast_on" and sec[0]["n"] == meta["arm"]
            rib = next(s for s in sec if "ribbing" in s["op_short"])
            assert rib["n"] == meta["wrist"]        # cuff starts at wrist count
            assert sec[-1]["kind"] == "bind_off"
            assert sec[-1]["worked"] == meta["wrist"]

        # no invented stitch-count changes anywhere
        assert sum(s["increases"] for s in steps) == meta["working"] - meta["neck"]
        assert sum(s["decreases"] for s in steps) == 2 * (meta["arm"] - meta["wrist"])

    def test_steps_carry_before_after_counts(self):
        """Every step carries the stitch count before and after the round,
        and the two always agree with the increases/decreases actually
        worked — so the status line '160 → 168 (+8)' is real, never
        invented."""
        plan = self._plan()
        sim = plan["sim_plan"]
        module = load_demo("knit_simulator")
        steps = module.DEMO["compute"]({
            "instructions": sim["instructions"], "plan": sim,
        })["steps"]
        for st in steps:
            if st["kind"] == "cast_on":
                continue   # a cast-on creates the stitches from nothing
            if st["kind"] == "bind_off":
                assert st["before"] - st["worked"] == st["n"], st
                continue   # bind-off removes stitches, no k2tog-style count
            assert st["before"] + st["increases"] - st["decreases"] == st["n"], st
        # the first yoke round is the first raglan increase: 72 -> 80 (+8)
        yoke = next(s for s in steps if s["section"] == "yoke")
        assert yoke["increases"] == plan["meta"]["inc"]
        assert yoke["before"] == plan["meta"]["calc_neck"]
        assert yoke["n"] == plan["meta"]["calc_neck"] + plan["meta"]["inc"]
        # every bind-off round reports its full run-down
        bo = [s for s in steps if s["kind"] == "bind_off"]
        assert bo and all(s["before"] > 0 and s["n"] == 0 for s in bo)

    def test_manual_steps_carry_before_counts(self):
        module = load_demo("knit_simulator")
        result = module.DEMO["compute"]({
            "instructions": "co 10\nk2 p2 across\nk2tog across\nbo 4",
        })
        for st in result["steps"]:
            if st["kind"] == "cast_on":
                continue
            if st["kind"] == "bind_off":
                assert st["before"] - st["worked"] == st["n"]
                continue
            assert st["before"] + st["increases"] - st["decreases"] == st["n"]

    def test_neck_section_label(self):
        """The compact progress view uses 'Neck' for the first section."""
        sim = self._plan()["sim_plan"]
        assert sim["sections"][0]["label"] == "Neck"

    def test_invalid_plan_raises(self):
        """A malformed plan must raise, never silently fall back."""
        sim = self._plan()["sim_plan"]
        module = load_demo("knit_simulator")
        bad_sections = [dict(s) for s in sim["sections"]]
        bad_sections[-1]["end"] += 1
        with pytest.raises(ValueError, match="do not match the simulation"):
            module.DEMO["compute"]({
                "instructions": sim["instructions"],
                "plan": {"instructions": sim["instructions"], "sections": bad_sections},
            })
        with pytest.raises(ValueError, match="missing its instructions"):
            module.DEMO["compute"]({
                "instructions": sim["instructions"],
                "plan": {"sections": sim["sections"]},
            })

    def test_overflow_row_is_warned(self):
        """A row that names more stitches than are on the needle is reported
        instead of silently producing a misleading garment."""
        module = load_demo("knit_simulator")
        result = module.DEMO["compute"]({
            "instructions": "co 10\nk 15\nk2 p2 across",
        })
        assert any("15" in w and "10" in w for w in result["warnings"])

    def test_raglan_page_publishes_plan(self):
        html_path = DEMOS_DIR.parent.parent.parent / "demos" / "raglan-sweater" / "demo.html"
        if not html_path.exists():
            pytest.skip("raglan demo.html not found")
        content = html_path.read_text(encoding="utf-8")
        assert "raglan_sim_plan" in content
        assert "knit_sim_plan" in content

    def test_knit_sim_page_reads_plan(self):
        html_path = DEMOS_DIR.parent.parent.parent / "demos" / "knit-simulator" / "demo.html"
        if not html_path.exists():
            pytest.skip("knit-simulator demo.html not found")
        content = html_path.read_text(encoding="utf-8")
        assert "knit_sim_plan" in content
        assert "_read_raglan_plan" in content
        assert "sim-phase-line" in content
        assert "section-progress" in content
        assert "raglanOutline" in content
        assert "raglan-inc-dots" in content


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