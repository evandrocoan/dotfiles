#!/usr/bin/env python3
"""
SmartGit tool: commit staged changes with oco, create a branch, push it,
and open a Merge Request on a self-hosted GitLab instance.

Requires env var:
  GITLAB_TOKEN  or  GITLAB_PAT  — GitLab personal access token
"""

import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
import urllib.error
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

GITLAB_URL = os.environ.get("GITLAB_URL", "https://gitlab.com")
DEFAULT_TARGET_BRANCH = "master"


def run(cmd):
    return subprocess.run(cmd, check=True, text=True, capture_output=True)


def get_token():
    token = os.environ.get("GITLAB_TOKEN") or os.environ.get("GITLAB_PAT")
    if not token:
        logger.error("GITLAB_TOKEN or GITLAB_PAT environment variable is not set.")
        sys.exit(1)
    return token


def get_current_branch():
    return run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()


def get_remote_project_path():
    url = run(["git", "remote", "get-url", "origin"]).stdout.strip()
    # SSH: git@gitlab.in.khomp.com:group/repo.git
    ssh_match = re.match(r"git@[^:]+:(.+?)(?:\.git)?$", url)
    if ssh_match:
        return ssh_match.group(1)
    # HTTPS: https://gitlab.in.khomp.com/group/repo.git
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.lstrip("/").removesuffix(".git")
    if path:
        return path
    logger.error("Could not parse project path from remote URL: {}", url)
    sys.exit(1)


def slugify(text):
    # strip conventional commit type prefix (feat:, fix:, etc.) for branch name
    text = re.sub(r"^[a-z]+(\([^)]+\))?!?:\s*", "", text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"-+", "-", text)
    return text[:72]


def gitlab_request(method, path, token, data=None):
    url = f"{GITLAB_URL}/api/v4{path}"
    headers = {
        "PRIVATE-TOKEN": token,
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        logger.error("GitLab API error {}: {}", e.code, body)
        sys.exit(1)


def main():
    # --- 1. run oco interactively (user sees prompt and confirms) ---
    logger.info("Running oco to commit staged changes...")
    result = subprocess.run(["oco", "--yes"])
    if result.returncode != 0:
        logger.warning("oco exited with an error or was cancelled. Proceeding anyway.")

    # --- 2. read commit message from git log ---
    commit_msg = run(["git", "log", "-1", "--format=%s"]).stdout.strip()
    if not commit_msg:
        logger.error("Could not read the last commit message.")
        sys.exit(1)
    logger.info("Commit: {}", commit_msg)

    # --- 3. suggest a branch name ---
    suggested = slugify(commit_msg)
    branch_input = input(f"Branch name (Enter for '{suggested}', or type a new one): ").strip()
    branch_name = branch_input if branch_input else suggested
    logger.info("Branch name: {}", branch_name)

    target_input = input(f"Target branch (Enter for '{DEFAULT_TARGET_BRANCH}', or type a new one): ").strip()
    target_branch = target_input if target_input else DEFAULT_TARGET_BRANCH

    # --- 4. create branch from current branch and push ---
    source_branch = get_current_branch()
    logger.info("Creating branch '{}' from '{}'...", branch_name, source_branch)
    subprocess.run(["git", "checkout", "-b", branch_name], check=True)

    logger.info("Pushing '{}' to origin...", branch_name)
    subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)

    # --- 5. resolve GitLab project ID ---
    token = get_token()
    project_path = get_remote_project_path()
    encoded_path = urllib.parse.quote(project_path, safe="")
    logger.info("Resolving GitLab project: {}", project_path)
    project = gitlab_request("GET", f"/projects/{encoded_path}", token)
    project_id = project["id"]

    # --- 6. create the MR ---
    logger.info("Creating Merge Request...")
    mr = gitlab_request(
        "POST",
        f"/projects/{project_id}/merge_requests",
        token,
        {
            "source_branch": branch_name,
            "target_branch": target_branch,
            "title": commit_msg,
            "remove_source_branch": True,
        },
    )

    logger.success("MR created: {}", mr["web_url"])
    input(f"Press Enter to open the MR in the browser {mr['web_url']}...")

    subprocess.run(["xdg-open", mr["web_url"]])


if __name__ == "__main__":
    main()
