"""Tests for scripts/calculate_version.py version calculation logic."""

import subprocess
from unittest.mock import patch

from scripts.calculate_version import (
    compute_bump_level,
    calculate_version,
    find_last_release_tag,
    has_test_changes,
    run_git,
)


class TestRunGit:
    """Test the run_git helper."""

    @patch("subprocess.run")
    def test_run_git_success(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["git", "rev-parse", "HEAD"],
            returncode=0,
            stdout="abc123\n",
            stderr="",
        )
        result = run_git("rev-parse", "HEAD")
        assert result == "abc123"
        mock_run.assert_called_once_with(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )

    @patch("subprocess.run")
    def test_run_git_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        try:
            run_git("bad-command")
            assert False, "Should have raised"
        except subprocess.CalledProcessError:
            pass


class TestFindLastReleaseTag:
    """Test release tag discovery."""

    @patch("scripts.calculate_version.run_git")
    def test_finds_tag(self, mock_git):
        mock_git.return_value = "v0.0.4\nv0.0.3\nv0.0.2"
        assert find_last_release_tag() == "v0.0.4"

    @patch("scripts.calculate_version.run_git")
    def test_no_tags(self, mock_git):
        mock_git.return_value = ""
        assert find_last_release_tag() is None

    @patch("scripts.calculate_version.run_git")
    def test_ignores_pre_release_tags(self, mock_git):
        mock_git.return_value = "v0.1.0-beta.1\nv0.0.4"
        assert find_last_release_tag() == "v0.0.4"


class TestHasTestChanges:
    """Test test-change detection."""

    def test_e2e_detected(self):
        files = ["test/end-to-end/test_docker_image.py", "pyknit/__init__.py"]
        assert has_test_changes(files, "test/end-to-end") is True

    def test_integration_detected(self):
        files = ["test/integration/qa_demos.py"]
        assert has_test_changes(files, "test/integration") is True

    def test_no_match(self):
        files = ["pyknit/Chart.py", "README.md"]
        assert has_test_changes(files, "test/end-to-end") is False

    def test_empty_list(self):
        assert has_test_changes([], "test/unit") is False


class TestComputeBumpLevel:
    """Test bump level computation logic."""

    def test_e2e_changes_give_major(self):
        files = ["test/end-to-end/test_docker_image.py"]
        assert compute_bump_level(files) == "major"

    def test_integration_changes_give_minor(self):
        files = ["test/integration/qa_demos.py"]
        assert compute_bump_level(files) == "minor"

    def test_no_test_changes_give_patch(self):
        files = ["pyknit/Chart.py", "README.md"]
        assert compute_bump_level(files) == "patch"

    def test_unit_test_changes_give_patch(self):
        files = ["test/unit/test_chart.py"]
        assert compute_bump_level(files) == "patch"

    def test_e2e_takes_priority_over_integration(self):
        files = ["test/end-to-end/test_docker_image.py", "test/integration/qa_demos.py"]
        assert compute_bump_level(files) == "major"

    def test_e2e_takes_priority_over_unit(self):
        files = ["test/end-to-end/test_docker_image.py", "test/unit/test_chart.py"]
        assert compute_bump_level(files) == "major"

    def test_integration_takes_priority_over_unit(self):
        files = ["test/integration/qa_demos.py", "test/unit/test_chart.py"]
        assert compute_bump_level(files) == "minor"

    def test_empty_files_give_patch(self):
        assert compute_bump_level([]) == "patch"


class TestCalculateVersion:
    """Integration-level tests for full version calculation."""

    @patch("scripts.calculate_version.run_git")
    def test_no_previous_tag(self, mock_git):
        mock_git.side_effect = [
            "abc1234567890",  # HEAD sha
            "",  # tags (empty)
            "pyknit/__init__.py\nREADME.md",  # changed files
        ]
        version = calculate_version()
        assert version == "0.0.1+abc12"

    @patch("scripts.calculate_version.run_git")
    def test_patch_bump(self, mock_git):
        mock_git.side_effect = [
            "def4567890123",  # HEAD sha
            "v0.1.4",  # last tag
            "pyknit/__init__.py",  # changed files (no test changes)
        ]
        version = calculate_version()
        assert version == "0.1.5+def45"

    @patch("scripts.calculate_version.run_git")
    def test_minor_bump(self, mock_git):
        mock_git.side_effect = [
            "1234567890abc",  # HEAD sha
            "v0.1.4",  # last tag
            "test/integration/qa_demos.py",  # changed files
        ]
        version = calculate_version()
        assert version == "0.2.0+12345"

    @patch("scripts.calculate_version.run_git")
    def test_major_bump(self, mock_git):
        mock_git.side_effect = [
            "abcdef1234567",  # HEAD sha
            "v0.1.4",  # last tag
            "test/end-to-end/test_docker_image.py",  # changed files
        ]
        version = calculate_version()
        assert version == "1.0.0+abcde"

    @patch("scripts.calculate_version.run_git")
    def test_unit_only_still_patch(self, mock_git):
        mock_git.side_effect = [
            "aaaaa11111bbbb",  # HEAD sha
            "v1.2.3",  # last tag
            "test/unit/test_chart.py",  # only unit test changed
        ]
        version = calculate_version()
        assert version == "1.2.4+aaaaa"

    @patch("scripts.calculate_version.run_git")
    def test_explicit_sha(self, mock_git):
        mock_git.side_effect = [
            "v1.0.0",  # last tag
            "pyknit/Chart.py",  # changed files
        ]
        version = calculate_version(sha="ffffff1234567890")
        assert version == "1.0.1+fffff"

    @patch("scripts.calculate_version.run_git")
    def test_major_from_zero(self, mock_git):
        mock_git.side_effect = [
            "deadbeef12345",  # HEAD sha
            "v0.0.0",  # last tag
            "test/end-to-end/test_docker_image.py",  # changed files
        ]
        version = calculate_version()
        assert version == "1.0.0+deadb"

    @patch("scripts.calculate_version.run_git")
    def test_minor_from_zero(self, mock_git):
        mock_git.side_effect = [
            "cafebabe12345",  # HEAD sha
            "v0.0.0",  # last tag
            "test/integration/qa_demos.py",  # changed files
        ]
        version = calculate_version()
        assert version == "0.1.0+cafeb"

    @patch("scripts.calculate_version.run_git")
    def test_sha_truncated_to_five(self, mock_git):
        mock_git.side_effect = [
            "v0.0.1",  # last tag
            "some_file.py",  # changed files
        ]
        version = calculate_version(sha="1234567890abcdef")
        assert version.endswith("+12345")
        assert len(version.split("+")[1]) == 5
