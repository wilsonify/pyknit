"""Tests for the native Android adapter around the canonical pyKnit demos."""

import importlib.util
import json
import pathlib

from pyknit.chaquopy import mobile_api as package_mobile_api


ROOT = pathlib.Path(__file__).resolve().parents[2]
BRIDGE = ROOT / "pyknit" / "chaquopy" / "mobile_api.py"


def _load_bridge():
    spec = importlib.util.spec_from_file_location("mobile_api_test", BRIDGE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_android_project_is_native_and_chaquopy_based():
    build = (ROOT / "android" / "app" / "build.gradle.kts").read_text()
    activity = (ROOT / "android" / "app" / "src" / "main" / "kotlin" / "org" / "pyknit" / "android" / "MainActivity.kt").read_text()
    assert "com.chaquo.python" in build
    assert "android.webkit.WebView" not in activity
    assert "Python.getInstance" in activity
    assert 'getModule("pyknit.chaquopy.mobile_api")' in activity


def test_bridge_is_importable_from_chaquopy_package():
    assert package_mobile_api.__name__ == "pyknit.chaquopy.mobile_api"
    assert callable(package_mobile_api.planner_to_simulator)


def test_raglan_instructions_are_exactly_what_simulator_executes():
    api = _load_bridge()
    payload = json.loads(api.planner_to_simulator("raglan", "{}"))
    plan = payload["sim_plan"]
    simulation = payload["simulation"]
    assert payload["instructions"] == plan["instructions"]
    assert simulation["garment"] == "raglan"
    assert simulation["sections"] == plan["sections"]
    assert simulation["steps"][0]["n"] == plan["counts"]["neck"]


def test_manual_edits_drop_stale_planner_sections():
    api = _load_bridge()
    payload = json.loads(api.planner_to_simulator("hat", "{}"))
    edited = payload["instructions"] + "k all\n"
    simulation = json.loads(api.build_simulation(edited, json.dumps(payload["sim_plan"])))
    assert "sections" not in simulation["simulation"]
    assert simulation["simulation"]["pattern"][-1] == "k all"


def test_sock_adapter_uses_calculator_rounds_without_recalculating():
    api = _load_bridge()
    payload = json.loads(api.planner_to_simulator("sock", "{}"))
    plan = payload["sim_plan"]
    simulation = payload["simulation"]
    assert plan["source"] == "sock_calculator"
    assert len(plan["rounds"]) == len(simulation["steps"])
    assert simulation["steps"][0]["n"] == plan["cast_on_stitches"]
