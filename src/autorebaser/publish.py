from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import re

from .report import write_report
from .util import RunError, clean_env, command, read_json, write_json


def publish(directory: Path, github_repo: str, *, base=None, source_ref=None, artifact_url=None):
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", github_repo):
        raise RunError("GitHub repository must be owner/name")
    state = read_json(directory / "run.json")
    if state["code_status"] != "passed":
        raise RunError("Only a validated candidate can be published")
    if artifact_url and not artifact_url.startswith("https://"):
        raise RunError("Artifact URL must be HTTPS")
    base, source_ref = base or state["target_ref"], source_ref or state["source_ref"]
    if any(not re.fullmatch(r"[\w./-]+", ref) or ref.startswith("-") or ".." in ref for ref in (base, source_ref)):
        raise RunError("Invalid publication branch")
    env = clean_env()
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if token:
        remote = f"https://github.com/{github_repo}.git"
        env.update(GH_TOKEN=token, GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",
                   GIT_CONFIG_VALUE_0="AUTHORIZATION: basic " + base64.b64encode(f"x-access-token:{token}".encode()).decode())
    else:
        remote = f"git@github.com:{github_repo}.git"
        if os.getenv("SSH_AUTH_SOCK"):
            env["SSH_AUTH_SOCK"] = os.environ["SSH_AUTH_SOCK"]
    repo = directory / "candidate"
    try:
        refs = command(["git", "ls-remote", "--heads", remote], repo, env=env)["output"]
        heads = {line.split()[1]: line.split()[0] for line in refs.splitlines()}
        if heads.get(f"refs/heads/{base}") != state["target"] or heads.get(f"refs/heads/{source_ref}") != state["source"]:
            state["publication_status"] = "stale"
            raise RunError("Remote source or target does not match the tested inputs; start a fresh run")
        existing_branch = heads.get(f"refs/heads/{state['branch']}")
        if existing_branch and existing_branch != state["candidate"]:
            raise RunError("The publication branch already has a different commit; refusing to overwrite it")
        command(["git", "push", remote, f"{state['candidate']}:refs/heads/{state['branch']}"], repo, env=env)
        status_args = ["gh", "api", "--method", "POST", f"repos/{github_repo}/statuses/{state['candidate']}",
                       "-f", "state=success", "-f", "context=Autorebaser / verified candidate",
                       "-f", f"description=Required checks passed on this commit; executor: {state.get('executor', 'unknown')}"]
        if artifact_url:
            status_args += ["-f", f"target_url={artifact_url}"]
        command(status_args, repo, env=env)
        body = (directory / "review.md").read_text()
        if artifact_url:
            body += f"\n\n[Download the video and evidence bundle]({artifact_url})\n"
        else:
            body += "\n\nThe full video/evidence bundle is available from the run operator; no hosted artifact URL was supplied.\n"
        body_file = directory / "pr-body.md"
        body_file.write_text(body)
        found = command(["gh", "pr", "list", "--repo", github_repo, "--head", state["branch"], "--base", base,
                         "--state", "all", "--json", "url,headRefOid,state"], repo, env=env)
        existing = json.loads(found["output"])
        if existing:
            if existing[0]["headRefOid"] != state["candidate"]:
                raise RunError("Existing PR points to a different candidate")
            url = existing[0]["url"]
        else:
            url = command(["gh", "pr", "create", "--repo", github_repo, "--head", state["branch"], "--base", base,
                           "--draft", "--title", f"Autorebase: preserve {source_ref} on {base}",
                           "--body-file", body_file], repo, env=env)["output"].strip()
        state.update(publication_status="published", pr_url=url, artifact_url=artifact_url)
        state.pop("publication_error", None)
        return url
    except Exception as exc:
        if state.get("publication_status") != "stale":
            state["publication_status"] = "failed"
        state["publication_error"] = str(exc)
        raise
    finally:
        write_json(directory / "run.json", state)
        write_report(directory)
