#!/usr/bin/env python3
"""Calculate deterministic SemVer version from git history.

Determines version bump level by analyzing test file changes since the last
release tag:

  - E2E test changes       → major bump (breaking/incompatible)
  - Integration test changes → minor bump (compatible API/behavior change)
  - No test changes         → patch bump (bug fix)
  - Unit-test-only changes  → patch bump (no major/minor forced)

Version format: MAJOR.MINOR.PATCH+<5-char-SHA>
Uniqueness guaranteed by commit SHA build metadata.

Usage:
    python scripts/calculate_version.py

Outputs the version string to stdout and sets GITHUB_OUTPUT if available.
"""

import os
import re
import subprocess
import sys


def run_git(*args: str) -> str:
    """Run a git command and return stripped stdout."""
    result = subprocess.run(
        ["git"] + list(args),
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def find_last_release_tag() -> str | None:
    """Find the most recent semver release tag (v*.*.*)."""
    try:
        tags = run_git("tag", "--list", "v*.*.*", "--sort=-version:refname")
    except subprocess.CalledProcessError:
        return None
    for tag in tags.splitlines():
        tag = tag.strip()
        if tag and re.match(r"^v\d+\.\d+\.\d+$", tag):
            return tag
    return None


def get_changed_files(ref: str | None = None) -> list[str]:
    """Return list of files changed since ref (or all files if ref is None)."""
    if ref is None:
        return run_git("ls-tree", "-r", "--name-only", "HEAD").splitlines()
    output = run_git("diff", "--name-only", ref, "HEAD")
    return output.splitlines() if output else []


def has_test_changes(files: list[str], pattern: str) -> bool:
    """Check if any file matches the given test path pattern."""
    return any(pattern in f for f in files)


def compute_bump_level(files: list[str]) -> str:
    """Determine SemVer bump level from changed test files.

    Priority: E2E > integration > patch.
    Unit-test-only changes get patch (never major/minor).
    """
    if has_test_changes(files, "test/end-to-end"):
        return "major"
    if has_test_changes(files, "test/integration"):
        return "minor"
    return "patch"


def calculate_version(sha: str | None = None) -> str:
    """Calculate the full SemVer version string.

    Args:
        sha: Full commit SHA. Defaults to HEAD.

    Returns:
        Version string in format MAJOR.MINOR.PATCH+5charSHA.
    """
    if sha is None:
        sha = run_git("rev-parse", "HEAD")
    short_sha = sha[:5]

    last_tag = find_last_release_tag()
    files = get_changed_files(last_tag)
    bump = compute_bump_level(files)

    if last_tag:
        base_version = last_tag.lstrip("v")
    else:
        base_version = "0.0.0"

    major, minor, patch = (int(x) for x in base_version.split("."))

    if bump == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1

    return f"{major}.{minor}.{patch}+{short_sha}"


def main() -> None:
    sha = sys.argv[1] if len(sys.argv) > 1 else None
    version = calculate_version(sha)
    print(version)

    # Set GITHUB_OUTPUT if running in GitHub Actions
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"version={version}\n")


if __name__ == "__main__":
    main()
