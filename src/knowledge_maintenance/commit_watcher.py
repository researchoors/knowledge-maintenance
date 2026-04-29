"""Commit watcher — detect new commits on a remote repository."""

import subprocess


def get_latest_commit(repo_url: str, branch: str = "main") -> str:
    """Return the latest commit SHA on *branch* of the remote *repo_url*.

    Uses git ls-remote to avoid cloning.
    """
    result = subprocess.run(
        ["git", "ls-remote", repo_url, f"refs/heads/{branch}"],
        capture_output=True,
        text=True,
        check=True,
    )
    # Output format: "<sha>\trefs/heads/<branch>"
    for line in result.stdout.strip().splitlines():
        sha, _ = line.split("\t", 1)
        return sha
    raise ValueError(f"Branch {branch!r} not found on {repo_url}")


def has_new_commits(repo_url: str, last_known: str, branch: str = "main") -> bool:
    """Return True if the remote has commits newer than *last_known* on *branch*."""
    latest = get_latest_commit(repo_url, branch=branch)
    return latest != last_known


def read_last_known(path: str = ".last_known_commit") -> str:
    """Read the last known commit SHA from a file, or empty string if not found."""
    try:
        return open(path).read().strip()
    except FileNotFoundError:
        return ""


def write_last_known(sha: str, path: str = ".last_known_commit") -> None:
    """Write the last known commit SHA to a file."""
    with open(path, "w") as f:
        f.write(sha)
