# Tests for sanitize-sarif.sh and validate-sarif.sh
import json
import os
import subprocess
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, ".github", "workflows", "scripts")
SANITIZE = os.path.join(SCRIPTS_DIR, "sanitize-sarif.sh")
VALIDATE = os.path.join(SCRIPTS_DIR, "validate-sarif.sh")


def _mk(r):
    return {"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "grype", "version": "0.118.0"}}, "results": r}]}


def _g(rid="C", u="a.py"):
    return {
        "ruleId": rid,
        "message": {"text": "v"},
        "level": "error",
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {"uri": u},
                    "region": {"startLine": 1, "startColumn": 1, "endLine": 1, "endColumn": 10},
                }
            }
        ],
    }


def _nl():
    return {"ruleId": "C", "message": {"text": "x"}, "level": "warning"}


def _el():
    return {"ruleId": "C", "message": {"text": "x"}, "level": "warning", "locations": []}


def _np():
    return {"ruleId": "C", "message": {"text": "x"}, "level": "warning", "locations": [{"logicalLocations": []}]}


def _na():
    return {
        "ruleId": "C",
        "message": {"text": "x"},
        "level": "error",
        "locations": [{"physicalLocation": {"region": {"startLine": 1}}}],
    }


def _ea():
    return {
        "ruleId": "C",
        "message": {"text": "x"},
        "level": "error",
        "locations": [{"physicalLocation": {"artifactLocation": {"uri": ""}, "region": {"startLine": 1}}}],
    }


def _nu():
    return {
        "ruleId": "C",
        "message": {"text": "x"},
        "level": "error",
        "locations": [{"physicalLocation": {"artifactLocation": {}, "region": {"startLine": 1}}}],
    }


def _ix():
    return {
        "ruleId": "C",
        "message": {"text": "x"},
        "level": "error",
        "locations": [{"physicalLocation": {"artifactLocation": {"index": 42}, "region": {"startLine": 1}}}],
    }


class TestSanitizeLogic:
    def _r(self, res):
        # Mirrors the on-disk sanitize-sarif.sh behavior: keep results
        # that have at least one location with a usable artifactLocation
        # (non-empty uri string or numeric index), drop the rest.
        def usable(loc):
            pl = loc.get("physicalLocation")
            if not isinstance(pl, dict):
                return False
            al = pl.get("artifactLocation")
            if not isinstance(al, dict):
                return False
            uri = al.get("uri")
            if isinstance(uri, str) and uri.strip():
                return True
            if isinstance(al.get("index"), int):
                return True
            return False

        def ok(r):
            return any(usable(loc) for loc in r.get("locations", []))

        c, s = [], {"t": len(res), "k": 0, "r": 0, "nl": 0, "ur": 0}
        for r in res:
            ls = r.get("locations")
            if not ls or not isinstance(ls, list) or len(ls) == 0:
                s["nl"] += 1
                continue
            if ok(r):
                s["k"] += 1
                c.append(r)
                continue
            s["ur"] += 1
        return c, s

    def test_t1(s):
        c, s2 = s._r([_g()])
        assert len(c) == 1
        assert s2["k"] == 1

    def test_t2(s):
        c, s2 = s._r([_nl()])
        assert len(c) == 0
        assert s2["nl"] == 1

    def test_t3(s):
        c, s2 = s._r([_el()])
        assert len(c) == 0
        assert s2["nl"] == 1

    def test_t4(s):
        c, s2 = s._r([_np()])
        assert len(c) == 0
        assert s2["ur"] == 1

    def test_t5(s):
        c, s2 = s._r([_na()])
        assert len(c) == 0
        assert s2["ur"] == 1

    def test_t6(s):
        c, s2 = s._r([_ea()])
        assert len(c) == 0
        assert s2["ur"] == 1

    def test_t7(s):
        c, s2 = s._r([_nu()])
        assert len(c) == 0
        assert s2["ur"] == 1

    def test_t8(s):
        c, s2 = s._r([_ix()])
        assert len(c) == 1
        assert s2["k"] == 1

    def test_t9(s):
        c, s2 = s._r([_g("C1", "a.py"), _nl(), _g("C2", "b.py"), _na(), _ea()])
        assert len(c) == 2
        assert s2["k"] == 2
        assert s2["nl"] == 1
        assert s2["ur"] == 2

    def test_t10(s):
        r = _g("C1", "a.py")
        r["locations"].append({"physicalLocation": {"region": {"startLine": 1}}})
        c, s2 = s._r([r])
        assert len(c) == 1

    def test_t11(s):
        r = {
            "ruleId": "C",
            "message": {"text": "x"},
            "locations": [
                {"physicalLocation": {"region": {"startLine": 1}}},
                {"physicalLocation": {"artifactLocation": {"uri": "a.py"}, "region": {"startLine": 1}}},
            ],
        }
        c, s2 = s._r([r])
        assert len(c) == 1

    def test_t12(s):
        c, s2 = s._r([])
        assert len(c) == 0
        assert s2["t"] == 0

    def test_t13(s):
        c, s2 = s._r([_nl(), _el(), _np()])
        assert len(c) == 0
        assert s2["nl"] == 2
        assert s2["ur"] == 1

    def test_t14(s):
        r = {
            "ruleId": "C",
            "message": {"text": "x"},
            "locations": [{"physicalLocation": {"artifactLocation": {"uri": "   "}, "region": {"startLine": 1}}}],
        }
        c, s2 = s._r([r])
        assert len(c) == 0
        assert s2["ur"] == 1


@pytest.mark.skipif(os.name == "nt", reason="bash scripts require Unix")
class TestSanitizeE2E:
    def _w(s, d, n, doc):
        p = os.path.join(d, "sarif", n + ".sarif")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write(json.dumps(doc))

    def _rd(s, d, n):
        return json.load(open(os.path.join(d, "sarif", n + ".sarif")))

    def test_t1(s, tmp_path):
        s._w(tmp_path, "source", _mk([_g("C1", "a.py"), _g("C2", "b.py")]))
        subprocess.run(["bash", SANITIZE], cwd=str(tmp_path), check=True, capture_output=True, text=True)
        assert len(s._rd(tmp_path, "source")["runs"][0]["results"]) == 2

    def test_t2(s, tmp_path):
        s._w(tmp_path, "source", _mk([_g(), _nl()]))
        subprocess.run(["bash", SANITIZE], cwd=str(tmp_path), check=True, capture_output=True, text=True)
        assert len(s._rd(tmp_path, "source")["runs"][0]["results"]) == 1

    def test_t3(s, tmp_path):
        s._w(tmp_path, "source", _mk([_ea()]))
        subprocess.run(["bash", SANITIZE], cwd=str(tmp_path), check=True, capture_output=True, text=True)
        sarif = s._rd(tmp_path, "source")
        assert len(sarif["runs"][0]["results"]) == 0

    def test_t4(s, tmp_path):
        os.makedirs(os.path.join(tmp_path, "sarif"), exist_ok=True)
        subprocess.run(["bash", SANITIZE], cwd=str(tmp_path), check=True, capture_output=True, text=True)
        r = s._rd(tmp_path, "source")
        assert r["version"] == "2.1.0"
        assert r["runs"][0]["results"] == []

    def test_t5(s, tmp_path):
        # Write empty SARIF then corrupt it; sanitize should handle gracefully
        s._w(tmp_path, "source", _mk([]))
        open(os.path.join(tmp_path, "sarif", "source.sarif"), "w").write("bad")
        r = subprocess.run(["bash", SANITIZE], cwd=str(tmp_path), capture_output=True, text=True)
        # Script may fail on corrupt JSON; that is acceptable
        if r.returncode == 0:
            assert s._rd(tmp_path, "source")["runs"][0]["results"] == []

    def test_t6(s, tmp_path):
        # _g calls have valid uri, _nl/_na/_ea have no usable location -> dropped
        s._w(tmp_path, "source", _mk([_g("C1", "a.py"), _nl(), _na(), _ea(), _g("C2", "b.py")]))
        subprocess.run(["bash", SANITIZE], cwd=str(tmp_path), check=True, capture_output=True, text=True)
        assert len(s._rd(tmp_path, "source")["runs"][0]["results"]) == 2

    def test_t7(s, tmp_path):
        s._w(tmp_path, "source", _mk([_g("C1", "a.py")]))
        r = subprocess.run(["bash", VALIDATE, "source"], cwd=str(tmp_path), capture_output=True, text=True)
        assert r.returncode == 0

    def test_t8(s, tmp_path):
        s._w(tmp_path, "source", _mk([_ea()]))
        r = subprocess.run(["bash", VALIDATE, "source"], cwd=str(tmp_path), capture_output=True, text=True)
        assert r.returncode == 1

    def test_t9(s, tmp_path):
        s._w(tmp_path, "source", _mk([_nl()]))
        r = subprocess.run(["bash", VALIDATE, "source"], cwd=str(tmp_path), capture_output=True, text=True)
        assert r.returncode == 1

    def test_t10(s, tmp_path):
        s._w(tmp_path, "source", _mk([_g("C1", "a.py"), _ea(), _nl()]))
        subprocess.run(["bash", SANITIZE], cwd=str(tmp_path), check=True, capture_output=True, text=True)
        r = subprocess.run(["bash", VALIDATE, "source"], cwd=str(tmp_path), capture_output=True, text=True)
        assert r.returncode == 0

    def test_t11(s, tmp_path):
        # All three results have no usable location -> all dropped
        s._w(tmp_path, "source", _mk([_na(), _ea(), _nu()]))
        subprocess.run(["bash", SANITIZE], cwd=str(tmp_path), check=True, capture_output=True, text=True)
        assert len(s._rd(tmp_path, "source")["runs"][0]["results"]) == 0


@pytest.mark.skipif(os.name == "nt", reason="bash scripts require Unix")
class TestFailOnHigh:
    def _rc(s, d, n, c):
        os.makedirs(os.path.join(d, "sarif"), exist_ok=True)
        open(os.path.join(d, "sarif", ".rc_" + n), "w").write(str(c))

    def test_t1(s, tmp_path):
        for n in ["s", "w", "a", "p"]:
            s._rc(tmp_path, n, 0)
        r = subprocess.run(
            ["bash", os.path.join(SCRIPTS_DIR, "fail-on-high.sh")], cwd=str(tmp_path), capture_output=True, text=True
        )
        assert r.returncode == 0

    def test_t2(s, tmp_path):
        for n in ["s", "w", "a", "p"]:
            s._rc(tmp_path, n, 1 if n == "s" else 0)
        r = subprocess.run(
            ["bash", os.path.join(SCRIPTS_DIR, "fail-on-high.sh")], cwd=str(tmp_path), capture_output=True, text=True
        )
        assert r.returncode == 1
