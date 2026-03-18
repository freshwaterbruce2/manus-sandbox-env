"""GitHub CLI wrapper for common automation tasks.

Provides a class-based interface over `gh` commands — repos, issues,
pull requests, releases, and branch operations. Designed for use
inside the Manus sandbox but works anywhere `gh` is authenticated.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from typing import Any


@dataclass
class CommandResult:
    """Result of a shell command execution."""

    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        """True if the command exited cleanly."""
        return self.returncode == 0

    def json(self) -> Any:
        """Parse stdout as JSON. Raises ValueError on bad input."""
        return json.loads(self.stdout)


def _run(cmd: list[str], *, check: bool = False) -> CommandResult:
    """Execute a command and return a structured result."""
    proc = subprocess.run(  # noqa: S603
        cmd,
        capture_output=True,
        text=True,
        check=check,
    )
    return CommandResult(
        returncode=proc.returncode,
        stdout=proc.stdout.strip(),
        stderr=proc.stderr.strip(),
    )


class GitHubHelper:
    """High-level wrapper around the GitHub CLI (gh)."""

    def __init__(self, repo: str | None = None) -> None:
        """Optionally bind to a specific owner/repo (e.g. 'user/repo')."""
        self.repo = repo

    def _repo_flag(self) -> list[str]:
        """Return ['--repo', 'owner/name'] if a repo is bound, else []."""
        return ["--repo", self.repo] if self.repo else []

    # ── Identity ─────────────────────────────────────────────────────

    def whoami(self) -> dict[str, Any]:
        """Return the authenticated GitHub user as a dict."""
        result = _run(["gh", "api", "user"])
        return result.json() if result.ok else {"error": result.stderr}

    # ── Repos ────────────────────────────────────────────────────────

    def list_repos(
        self,
        *,
        limit: int = 10,
        visibility: str = "all",
    ) -> list[dict[str, Any]]:
        """List repos for the authenticated user.

        Args:
            limit: Max repos to return (default 10).
            visibility: 'public', 'private', or 'all'.

        Returns:
            List of repo metadata dicts.

        """
        result = _run([
            "gh", "repo", "list",
            "--limit", str(limit),
            "--visibility", visibility,
            "--json", "name,description,visibility,updatedAt,url",
        ])
        return result.json() if result.ok else []

    def get_repo_info(self, repo: str | None = None) -> dict[str, Any]:
        """Fetch metadata for a single repository.

        Args:
            repo: 'owner/name' override. Falls back to self.repo.

        Returns:
            Dict with name, description, visibility, url, stars, forks.

        """
        target = repo or self.repo or "."
        result = _run([
            "gh", "repo", "view", target,
            "--json", "name,description,isPrivate,url,stargazerCount,forkCount",
        ])
        return result.json() if result.ok else {"error": result.stderr}

    def create_repo(
        self,
        name: str,
        *,
        private: bool = True,
        description: str = "",
    ) -> str:
        """Create a new GitHub repository.

        Args:
            name: Repository name.
            private: Whether the repo is private (default True).
            description: One-line repo description.

        Returns:
            URL of the created repo, or error string.

        """
        cmd = ["gh", "repo", "create", name, "--confirm"]
        if private:
            cmd.append("--private")
        else:
            cmd.append("--public")
        if description:
            cmd.extend(["--description", description])
        result = _run(cmd)
        return result.stdout if result.ok else f"Error: {result.stderr}"

    # ── Issues ───────────────────────────────────────────────────────

    def create_issue(
        self,
        title: str,
        *,
        body: str = "",
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
    ) -> str:
        """Create an issue and return its URL.

        Args:
            title: Issue title.
            body: Issue body (markdown).
            labels: Optional label names.
            assignees: Optional GitHub usernames.

        Returns:
            Issue URL or error string.

        """
        cmd = ["gh", "issue", "create", "--title", title]
        cmd.extend(self._repo_flag())
        if body:
            cmd.extend(["--body", body])
        if labels:
            cmd.extend(["--label", ",".join(labels)])
        if assignees:
            cmd.extend(["--assignee", ",".join(assignees)])
        result = _run(cmd)
        return result.stdout if result.ok else f"Error: {result.stderr}"

    def list_issues(
        self,
        *,
        state: str = "open",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """List issues for the bound repo.

        Args:
            state: 'open', 'closed', or 'all'.
            limit: Max issues to return.

        Returns:
            List of issue dicts.

        """
        cmd = [
            "gh", "issue", "list",
            "--state", state,
            "--limit", str(limit),
            "--json", "number,title,state,author,createdAt,url",
        ]
        cmd.extend(self._repo_flag())
        result = _run(cmd)
        return result.json() if result.ok else []

    # ── Pull Requests ────────────────────────────────────────────────

    def create_pr(
        self,
        title: str,
        *,
        body: str = "",
        base: str = "main",
        draft: bool = False,
    ) -> str:
        """Create a pull request from the current branch.

        Args:
            title: PR title.
            body: PR description (markdown).
            base: Target branch (default 'main').
            draft: Open as draft PR.

        Returns:
            PR URL or error string.

        """
        cmd = [
            "gh", "pr", "create",
            "--title", title,
            "--base", base,
        ]
        cmd.extend(self._repo_flag())
        if body:
            cmd.extend(["--body", body])
        if draft:
            cmd.append("--draft")
        result = _run(cmd)
        return result.stdout if result.ok else f"Error: {result.stderr}"

    def list_prs(
        self,
        *,
        state: str = "open",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """List pull requests.

        Args:
            state: 'open', 'closed', 'merged', or 'all'.
            limit: Max PRs to return.

        Returns:
            List of PR dicts.

        """
        cmd = [
            "gh", "pr", "list",
            "--state", state,
            "--limit", str(limit),
            "--json", "number,title,state,author,createdAt,url,headRefName",
        ]
        cmd.extend(self._repo_flag())
        result = _run(cmd)
        return result.json() if result.ok else []

    def merge_pr(
        self,
        pr_number: int,
        *,
        method: str = "squash",
        delete_branch: bool = True,
    ) -> str:
        """Merge a pull request.

        Args:
            pr_number: PR number to merge.
            method: 'merge', 'squash', or 'rebase'.
            delete_branch: Delete head branch after merge.

        Returns:
            Success message or error string.

        """
        cmd = [
            "gh", "pr", "merge", str(pr_number),
            f"--{method}",
        ]
        cmd.extend(self._repo_flag())
        if delete_branch:
            cmd.append("--delete-branch")
        result = _run(cmd)
        return result.stdout if result.ok else f"Error: {result.stderr}"

    # ── Releases ─────────────────────────────────────────────────────

    def create_release(
        self,
        tag: str,
        *,
        title: str = "",
        notes: str = "",
        draft: bool = False,
        prerelease: bool = False,
    ) -> str:
        """Create a GitHub release.

        Args:
            tag: Git tag for the release (e.g. 'v1.5.0').
            title: Release title (defaults to tag).
            notes: Release notes (markdown).
            draft: Create as draft.
            prerelease: Mark as pre-release.

        Returns:
            Release URL or error string.

        """
        cmd = ["gh", "release", "create", tag]
        cmd.extend(self._repo_flag())
        if title:
            cmd.extend(["--title", title])
        if notes:
            cmd.extend(["--notes", notes])
        if draft:
            cmd.append("--draft")
        if prerelease:
            cmd.append("--prerelease")
        result = _run(cmd)
        return result.stdout if result.ok else f"Error: {result.stderr}"

    def list_releases(self, *, limit: int = 10) -> list[dict[str, Any]]:
        """List releases for the bound repo.

        Args:
            limit: Max releases to return.

        Returns:
            List of release dicts.

        """
        cmd = [
            "gh", "release", "list",
            "--limit", str(limit),
        ]
        cmd.extend(self._repo_flag())
        # gh release list doesn't support --json, parse manually
        result = _run(cmd)
        if not result.ok:
            return []
        releases: list[dict[str, Any]] = []
        for line in result.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) >= 3:
                releases.append({
                    "tag": parts[0],
                    "title": parts[1] if len(parts) > 1 else "",
                    "date": parts[2] if len(parts) > 2 else "",
                })
        return releases

    # ── Branches ─────────────────────────────────────────────────────

    def list_branches(self) -> list[str]:
        """List remote branches for the bound repo.

        Returns:
            List of branch names.

        """
        cmd = ["gh", "api", f"repos/{self.repo}/branches", "--jq", ".[].name"]
        result = _run(cmd)
        return result.stdout.splitlines() if result.ok else []

    def delete_branch(self, branch: str) -> str:
        """Delete a remote branch.

        Args:
            branch: Branch name to delete.

        Returns:
            Success message or error string.

        """
        cmd = [
            "gh", "api",
            "-X", "DELETE",
            f"repos/{self.repo}/git/refs/heads/{branch}",
        ]
        result = _run(cmd)
        return f"Deleted {branch}" if result.ok else f"Error: {result.stderr}"

    # ── Workflows ────────────────────────────────────────────────────

    def list_workflow_runs(
        self,
        *,
        limit: int = 5,
        workflow: str | None = None,
    ) -> list[dict[str, Any]]:
        """List recent workflow runs.

        Args:
            limit: Max runs to return.
            workflow: Optional workflow filename filter (e.g. 'ci.yml').

        Returns:
            List of run dicts.

        """
        cmd = [
            "gh", "run", "list",
            "--limit", str(limit),
            "--json", "databaseId,displayTitle,status,conclusion,createdAt,url",
        ]
        cmd.extend(self._repo_flag())
        if workflow:
            cmd.extend(["--workflow", workflow])
        result = _run(cmd)
        return result.json() if result.ok else []


# ── CLI Demo ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    gh = GitHubHelper()
    user = gh.whoami()
    print(f"Authenticated as: {user.get('login', 'unknown')}")

    info = gh.get_repo_info()
    print(f"Current repo: {info.get('name', 'N/A')}")

    repos = gh.list_repos(limit=5)
    print(f"\nRecent repos ({len(repos)}):")
    for r in repos:
        print(f"  {r['name']} — {r.get('description', 'no description')}")

    sys.exit(0)
