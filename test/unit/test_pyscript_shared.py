import types

from pyknit.pyscript._assets import shared


class _Recorder:
    def __init__(self):
        self.status = []
        self.html = []
        self.errors = []
        self.trace = 0


def test_wire_demo_accepts_module_object_with_demo_dict(monkeypatch):
    rec = _Recorder()

    demo_module = types.SimpleNamespace(
        DEMO={
            "TITLE": "Demo X",
            "DEFAULT_INPUTS": {"n": 1},
            "compute": lambda inputs: {"n": int(inputs["n"]) + 1},
            "to_html": lambda result: f"<p>{result['n']}</p>",
        }
    )

    monkeypatch.setattr(shared, "collect_inputs", lambda defaults: {"n": "2"})
    monkeypatch.setattr(shared, "set_status", lambda *args: rec.status.append(args))
    monkeypatch.setattr(shared, "set_html", lambda _eid, html: rec.html.append(html))
    monkeypatch.setattr(shared, "hide_error", lambda _eid: None)
    monkeypatch.setattr(shared, "show_error", lambda _eid, msg: rec.errors.append(msg))

    handler = shared.wire_demo(demo_module)
    handler()

    assert rec.errors == []
    assert rec.html[-1] == "<p>3</p>"
    assert rec.status[-1][0] == "ready"
    assert "updated" in rec.status[-1][1]


def test_wire_demo_value_error_does_not_log_traceback(monkeypatch):
    rec = _Recorder()

    demo = {
        "TITLE": "Validation Demo",
        "DEFAULT_INPUTS": {"x": 1},
        "compute": lambda _inputs: (_ for _ in ()).throw(ValueError("bad input")),
    }

    monkeypatch.setattr(shared, "collect_inputs", lambda defaults: {"x": "bad"})
    monkeypatch.setattr(shared, "set_status", lambda *args: rec.status.append(args))
    monkeypatch.setattr(shared, "show_error", lambda _eid, msg: rec.errors.append(msg))
    monkeypatch.setattr(shared, "hide_error", lambda _eid: None)
    monkeypatch.setattr(shared, "_log_unexpected_error", lambda: setattr(rec, "trace", rec.trace + 1))

    shared.wire_demo(demo)()

    assert rec.trace == 0
    assert rec.errors == ["bad input"]
    assert rec.status[-1][0] == "ready"
    assert rec.status[-1][1] == "Please check your inputs"


def test_wire_demo_unexpected_error_logs_traceback(monkeypatch):
    rec = _Recorder()

    demo = {
        "TITLE": "Crash Demo",
        "DEFAULT_INPUTS": {"x": 1},
        "compute": lambda _inputs: (_ for _ in ()).throw(RuntimeError("boom")),
    }

    monkeypatch.setattr(shared, "collect_inputs", lambda defaults: {"x": "1"})
    monkeypatch.setattr(shared, "set_status", lambda *args: rec.status.append(args))
    monkeypatch.setattr(shared, "show_error", lambda _eid, msg: rec.errors.append(msg))
    monkeypatch.setattr(shared, "hide_error", lambda _eid: None)
    monkeypatch.setattr(shared, "_log_unexpected_error", lambda: setattr(rec, "trace", rec.trace + 1))

    shared.wire_demo(demo)()

    assert rec.trace == 1
    assert rec.status[-1][0] == "error"
    assert rec.errors == ["boom"]


def test_bootstrap_demo_binds_and_autoruns(monkeypatch):
    rec = _Recorder()

    monkeypatch.setattr(shared, "set_status", lambda *args: rec.status.append(args))
    monkeypatch.setattr(shared, "bind_click", lambda _bid, _handler: rec.status.append(("bound",)))
    monkeypatch.setattr(shared, "wire_demo", lambda _module=None: (lambda _event=None: rec.html.append("ran")))

    shared.bootstrap_demo(module={"DEFAULT_INPUTS": {}, "compute": lambda _x: {}}, action_label="Run", auto_run=True)

    assert ("bound",) in rec.status
    assert rec.html == ["ran"]
