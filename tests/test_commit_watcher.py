"""Tests for commit watcher."""

from unittest.mock import MagicMock, patch

from knowledge_maintenance.commit_watcher import get_latest_commit, has_new_commits, read_last_known, write_last_known


class TestGetLatestCommit:
    @patch("knowledge_maintenance.commit_watcher.subprocess.run")
    def test_returns_sha(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(stdout="abc123def456\trefs/heads/main\n")
        sha = get_latest_commit("https://github.com/org/repo", branch="main")
        assert sha == "abc123def456"

    @patch("knowledge_maintenance.commit_watcher.subprocess.run")
    def test_raises_on_empty_output(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(stdout="")
        try:
            get_latest_commit("https://github.com/org/repo", branch="nonexistent")
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "nonexistent" in str(e)


class TestHasNewCommits:
    @patch("knowledge_maintenance.commit_watcher.get_latest_commit")
    def test_same_sha_returns_false(self, mock_get: MagicMock) -> None:
        mock_get.return_value = "abc123"
        assert has_new_commits("https://github.com/org/repo", "abc123") is False

    @patch("knowledge_maintenance.commit_watcher.get_latest_commit")
    def test_different_sha_returns_true(self, mock_get: MagicMock) -> None:
        mock_get.return_value = "def456"
        assert has_new_commits("https://github.com/org/repo", "abc123") is True


class TestLastKnownFile:
    def test_read_missing_file(self, tmp_path) -> None:
        path = str(tmp_path / "nonexistent")
        assert read_last_known(path) == ""

    def test_write_and_read(self, tmp_path) -> None:
        path = str(tmp_path / "sha.txt")
        write_last_known("abc123", path)
        assert read_last_known(path) == "abc123"
