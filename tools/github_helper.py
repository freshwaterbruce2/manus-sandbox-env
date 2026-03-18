#!/usr/bin/env python3
"""
github_helper.py — Reusable GitHub CLI wrapper for the Manus sandbox.

Provides convenience functions around common `gh` CLI operations so that
other scripts don't need to repeat subprocess boilerplate.
"""

import subprocess
import json
from typing import Optional


def _run(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    """Execute a shell command and return the CompletedProcess result."""
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)


def get_authenticated_user() -> dict:
    """Return the currently authenticated GitHub user as a dict."""
    result = _run("gh api user")
    return json.loads(result.stdout)


def list_repos(limit: int = 10, visibility: str = "all") -> list[dict]:
    """
    List repositories for the authenticated user.

    Args:
        limit: Maximum number of repos to return.
        visibility: One of 'all', 'public', 'private'.

    Returns:
        List of repo dicts with keys: name, isPrivate, description, updatedAt.
    """
    jq = ".[] | {name, isPrivate, description, updatedAt}"
    result = _run(
        f"gh repo list --limit {limit} --visibility {visibility} "
        f"--json name,isPrivate,description,updatedAt --jq '[{jq}]'"
    )
    return json.loads(result.stdout)


def create_issue(title: str, body: str, repo: Optional[str] = None) -> str:
    """
    Create a GitHub issue and return its URL.

    Args:
        title: Issue title.
        body: Issue body (Markdown supported).
        repo: Optional repo in 'owner/name' format; defaults to current repo.

    Returns:
        URL of the created issue.
    """
    repo_flag = f"--repo {repo}" if repo else ""
    result = _run(f'gh issue create {repo_flag} --title "{title}" --body "{body}"')
    return result.stdout.strip()


def create_pr(title: str, body: str, base: str = "main") -> str:
    """
    Create a pull request from the current branch and return its URL.

    Args:
        title: PR title.
        body: PR body (Markdown supported).
        base: Base branch to merge into.

    Returns:
        URL of the created pull request.
    """
    result = _run(
        f'gh pr create --title "{title}" --body "{body}" --base {base}'
    )
    return result.stdout.strip()


def get_repo_info(repo: Optional[str] = None) -> dict:
    """
    Return metadata about a repository.

    Args:
        repo: Optional repo in 'owner/name' format; defaults to current repo.

    Returns:
        Dict with repo metadata.
    """
    repo_flag = f"--repo {repo}" if repo else ""
    result = _run(f"gh repo view {repo_flag} --json name,description,isPrivate,url,stargazerCount,forkCount")
    return json.loads(result.stdout)


if __name__ == "__main__":
    print("=== GitHub Helper Demo ===\n")

    user = get_authenticated_user()
    print(f"Authenticated as : {user['login']}")
    print(f"Public repos     : {user.get('public_repos', 'N/A')}\n")

    info = get_repo_info()
    print(f"Current repo     : {info['name']}")
    print(f"Description      : {info.get('description', 'N/A')}")
    print(f"Private          : {info['isPrivate']}")
    print(f"URL              : {info['url']}\n")

    repos = list_repos(limit=5)
    print("Recent repos:")
    for r in repos:
        vis = "private" if r["isPrivate"] else "public"
        print(f"  [{vis:7s}] {r['name']}")
