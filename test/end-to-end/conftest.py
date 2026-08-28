import os
import shutil
import socket
import subprocess
import time
import urllib.request
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
IMAGE = os.environ.get("PYKNIT_DEMO_IMAGE", "pyknit-demos:test")
DOCKERFILE = REPO_ROOT / "demos" / "Dockerfile"
CONTAINER = "pyknit-demos-e2e"


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def demo_url():
    docker = shutil.which("docker")
    if docker is None:
        pytest.skip("docker CLI not available")
    build = subprocess.run(
        ["docker", "build", "-t", IMAGE, "-f", str(DOCKERFILE), str(REPO_ROOT)],
        capture_output=True,
        text=True,
    )
    if build.returncode != 0:
        pytest.fail(f"docker build failed:\n{build.stdout}\n{build.stderr[-2000:]}")
    port = _free_port()
    subprocess.run(["docker", "rm", "-f", CONTAINER], capture_output=True)
    run = subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            CONTAINER,
            "-p",
            f"127.0.0.1:{port}:8080",
            IMAGE,
        ],
        capture_output=True,
        text=True,
    )
    if run.returncode != 0:
        pytest.fail(f"docker run failed:\n{run.stderr[-1000:]}")
    url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url + "/index.html", timeout=2) as r:
                if r.status == 200:
                    break
        except Exception:
            time.sleep(0.5)
    else:
        subprocess.run(["docker", "rm", "-f", CONTAINER], capture_output=True)
        pytest.fail("container did not become ready")
    yield url
    subprocess.run(["docker", "rm", "-f", CONTAINER], capture_output=True)


@pytest.fixture(scope="session")
def browser():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip("playwright is not installed")
    with sync_playwright() as p:
        try:
            b = p.chromium.launch(headless=True)
        except Exception:
            pytest.skip("chromium is not installed for playwright")
        yield b
        b.close()
