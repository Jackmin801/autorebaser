from __future__ import annotations

import json
from pathlib import Path
import re
import time

from .model import Model, PATCH_SCHEMA, STORY_SCHEMA
from .runner import Runner
from .util import Journal, RunError, digest, git, git_text, read_json, safe_file, write_json


def resolve(repo, ref):
    if not re.fullmatch(r"[\w./-]+", ref) or ref.startswith("-") or ".." in ref:
        raise RunError(f"Invalid Git ref: {ref}")
    for candidate in (f"refs/remotes/origin/{ref}", ref):
        result = git(repo, "rev-parse", "--verify", f"{candidate}^{{commit}}", check=False)
        if result["exit_code"] == 0:
            return result["output"].strip()
    raise RunError(f"Cannot resolve commit: {ref}")


def files(repo):
    result = {}
    for name in git_text(repo, "ls-files").splitlines():
        if name.endswith((".py", ".md", ".json", ".lock", ".toml")):
            path = safe_file(repo, name)
            if path.exists() and path.stat().st_size < 80000:
                result[name] = path.read_text()
    if sum(map(len, result.values())) > 350000:
        raise RunError("Repository context exceeds the MVP limit (350,000 characters)")
    return result


def patch(repo, proposal, roots):
    changes = proposal.get("changes", [])
    if not changes or len(changes) > 15:
        raise RunError("A repair must change between 1 and 15 source files")
    prepared = []
    seen = set()
    for change in changes:
        name, content = change["path"], change["content"]
        path = safe_file(repo, name)
        if name in seen or not any(name.startswith(root) for root in roots) or not name.endswith(".py"):
            raise RunError(f"Repair cannot edit {name}; only Python files under {roots} are allowed")
        if "test" in Path(name).parts or "tests" in Path(name).parts or Path(name).name.startswith("test_"):
            raise RunError(f"The repair agent cannot edit tests: {name}")
        if len(content) > 100000:
            raise RunError(f"Proposed file is too large: {name}")
        compile(content, name, "exec")
        seen.add(name)
        prepared.append((path, content))
    for path, content in prepared:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


def protected(repo, roots):
    return {name: digest((repo / name).read_bytes()) for name in git_text(repo, "ls-files").splitlines()
            if not any(name.startswith(root) for root in roots)}


def validate_story(story, evidence):
    valid = {claim["id"] for claim in evidence["claims"]}
    if not isinstance(story.get("title"), str) or len(story["title"]) > 90:
        raise RunError("Storyboard title is missing or too long")
    scenes = story.get("scenes", [])
    if len(scenes) != 4:
        raise RunError("Storyboard must contain four scenes")
    for scene in scenes:
        if not isinstance(scene.get("title"), str) or not isinstance(scene.get("caption"), str):
            raise RunError("Storyboard text must be strings")
        if len(scene["title"]) > 70 or len(scene["caption"]) > 280:
            raise RunError("Storyboard text exceeds scene layout limits")
        if not scene.get("evidence_ids") or not set(scene["evidence_ids"]) <= valid:
            raise RunError("Storyboard refers to missing evidence")
    return story


def run_rebase(repo_url: str, source: str, onto: str, output: Path, *, provider="auto",
               executor="docker", max_repairs=3, render=True, demo=False, config_path=None):
    output = output.resolve()
    if output.exists() and any(output.iterdir()):
        raise RunError(f"Run directory must be new: {output}")
    output.mkdir(parents=True, exist_ok=True)
    (output / "patches").mkdir()
    log = Journal(output)
    state = {"run_id": output.name, "repo": repo_url, "source_ref": source, "target_ref": onto,
             "code_status": "running", "video_status": "pending" if render else "skipped",
             "publication_status": "not_requested", "executor": executor, "repairs": [], "checks": []}
    write_json(output / "run.json", state)
    repo = output / "candidate"
    started = time.monotonic()
    try:
        log.emit("prepare", "Cloning an isolated copy and pinning the branch heads")
        git(output, "clone", "--no-hardlinks", "--no-checkout", "--", repo_url, str(repo))
        head, target = resolve(repo, source), resolve(repo, onto)
        bases = git_text(repo, "merge-base", "--all", head, target).splitlines()
        if len(bases) != 1:
            raise RunError("Exactly one merge base is required")
        base = bases[0]
        if git_text(repo, "rev-list", "--merges", f"{base}..{head}"):
            raise RunError("Merge commits on the feature branch are outside the MVP scope")
        originals = git_text(repo, "rev-list", "--reverse", f"{base}..{head}").splitlines()
        if not originals:
            raise RunError("There are no feature commits to replay")
        config = read_json(config_path) if config_path else json.loads(git_text(repo, "show", f"{target}:autorebaser.json"))
        roots = config["editable_roots"]
        if not roots or any(not re.fullmatch(r"[\w-]+(?:/[\w-]+)*/", root) for root in roots):
            raise RunError("editable_roots must be explicit relative directory prefixes, e.g. app/")
        if not isinstance(config["test_command"], list) or not config["test_command"]:
            raise RunError("A nonempty test_command argument list is required")
        safe_file(repo, config["requirements"])
        state.update(source=head, target=target, base=base, intent=config.get("intent", "Preserve the feature behavior"),
                     branch=f"codex/autorebase/{output.name}")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", output.name):
            raise RunError("Run directory name must use letters, numbers, hyphens or underscores")
        write_json(output / "request.json", {**state, "config": config})
        for name, before, after in (("upstream", base, target), ("feature", base, head)):
            (output / "patches" / f"{name}.diff").write_text(git_text(repo, "diff", before, after))

        runner = Runner(output, config, executor)
        model = Model(output, provider)
        state["provider"] = model.provider
        state["model"] = model.model
        for label, sha in (("original", head), ("target", target)):
            location = output / label
            git(repo, "worktree", "add", "--detach", str(location), sha)
            log.emit("baseline", f"Checking {label} at {sha[:8]} in its own dependency environment")
            results = runner.check(location, label, sha, witness=demo and label == "original")
            state["checks"] = runner.checks
            if not all(c["passed"] for c in results):
                state["code_status"] = "baseline_failed"
                raise RunError(f"{label} baseline failed; refusing to attribute this to a rebase")

        git(repo, "checkout", "-b", state["branch"], head)
        log.emit("replay", f"Replaying {len(originals)} feature commits onto {target[:8]}")
        result = git(repo, "rebase", "--merge", "--reapply-cherry-picks", "--empty=stop", "--onto", target, base, check=False)

        def ask_repair(failures, phase):
            if len(state["repairs"]) >= max_repairs:
                raise RunError(f"Repair budget exhausted after {max_repairs} proposals")
            log.emit("astra", f"Diagnosing {phase} and proposing a minimal source repair")
            context = {"intent": state["intent"], "phase": phase, "editable_roots": roots,
                       "upstream_diff": (output / "patches/upstream.diff").read_text(),
                       "original_feature_diff": (output / "patches/feature.diff").read_text(),
                       "current_files": files(repo), "observed_failures": failures,
                       "previous_repairs": state["repairs"]}
            proposal = model.generate(json.dumps(context), PATCH_SCHEMA, "propose_repair")
            record = {"phase": phase, **proposal}
            state["repairs"].append(record)
            patch(repo, proposal, roots)
            log.emit("repair", proposal["summary"], paths=[c["path"] for c in proposal["changes"]])

        while result["exit_code"]:
            conflicts = git_text(repo, "diff", "--name-only", "--diff-filter=U").splitlines()
            if not conflicts:
                raise RunError("Replay stopped without editable conflicts (possibly an empty commit): " + result["output"])
            before = protected(repo, roots)
            ask_repair([{"git_output": result["output"], "conflicts": conflicts}], "Git conflict")
            if protected(repo, roots) != before:
                raise RunError("Protected files changed during conflict repair")
            git(repo, "add", "--", *[c["path"] for c in state["repairs"][-1]["changes"]])
            result = git(repo, "rebase", "--continue", check=False)

        integrated = git_text(repo, "rev-parse", "HEAD")
        rebased = git_text(repo, "rev-list", "--reverse", f"{target}..{integrated}").splitlines()
        if len(rebased) != len(originals):
            raise RunError("Feature commit count changed; manual review is required")
        write_json(output / "commits.json", [{"original": a, "rebased": b,
                                               "subject": git_text(repo, "show", "-s", "--format=%s", a)}
                                              for a, b in zip(originals, rebased)])
        state["integrated"] = integrated
        protected_files = protected(repo, roots)
        log.emit("test", "Checking the replayed feature, including behavior after process exit")
        current = runner.check(repo, "integration", integrated, witness=demo)

        if demo:
            control = output / "mechanical-control"
            git(repo, "worktree", "add", "--detach", str(control), integrated)
            for name in git_text(control, "ls-files", "app").splitlines():
                if name.endswith(".py"):
                    p = control / name
                    p.write_text(p.read_text().replace("from app.db import", "from app.storage.db import"))
            git(control, "add", "app")
            git(control, "commit", "--allow-empty", "-m", "Control: update import paths only (scripted)")
            log.emit("control", "Running the separately labeled import-only comparison")
            runner.check(control, "mechanical-control", git_text(control, "rev-parse", "HEAD"), witness=True)

        while not all(c["passed"] for c in current):
            ask_repair([{k: c[k] for k in ("id", "exit_code", "output")} for c in current if not c["passed"]], "behavior validation")
            if protected(repo, roots) != protected_files:
                raise RunError("A protected test, config, or dependency file changed")
            if not git_text(repo, "diff"):
                raise RunError("Proposed repair made no changes")
            git(repo, "add", "--", *[c["path"] for c in state["repairs"][-1]["changes"]])
            git(repo, "commit", "-m", f"Adapt feature after rebase: {state['repairs'][-1]['summary'][:100]}")
            current = runner.check(repo, f"repair-{len(state['repairs'])}", git_text(repo, "rev-parse", "HEAD"), witness=demo)

        candidate = git_text(repo, "rev-parse", "HEAD")
        # Test a fresh checkout of precisely the commit we will publish.
        final_dir = output / "verified"
        git(repo, "worktree", "add", "--detach", str(final_dir), candidate)
        log.emit("verify", f"Verifying the committed candidate {candidate[:8]} from a fresh checkout")
        final = runner.check(final_dir, "final", candidate, witness=demo)
        if not all(c["passed"] for c in final) or protected(repo, roots) != protected_files:
            raise RunError("Final committed-candidate verification failed")
        if git_text(repo, "status", "--porcelain") or git_text(final_dir, "status", "--porcelain"):
            raise RunError("Checks modified the candidate checkout")
        state.update(candidate=candidate, code_status="passed", checks=runner.checks)
        for name, before, after in (("candidate", target, candidate), ("repair", integrated, candidate)):
            (output / "patches" / f"{name}.diff").write_text(git_text(repo, "diff", before, after))
        (output / "patches/range-diff.txt").write_text(git_text(repo, "range-diff", f"{base}..{head}", f"{target}..{candidate}"))
        claims = [
            {"id": "upstream", "statement": "Changes made on the target branch", "support": "observed", "artifact": "patches/upstream.diff"},
            {"id": "feature", "statement": state["intent"], "support": "specified", "artifact": "patches/feature.diff"},
            {"id": "repair", "statement": "Candidate source adaptations", "support": "observed", "artifact": "patches/repair.diff"},
        ]
        claims += [{"id": c["id"], "statement": f"{c['label']} {c['kind']}: {'passed' if c['passed'] else 'failed'}",
                    "support": "observed", "artifact": f"checks/{c['id']}.json"} for c in runner.checks]
        evidence = {"candidate": candidate, "claims": claims, "checks": runner.checks,
                    "repairs": state["repairs"], "commits": read_json(output / "commits.json"),
                    "patches": {name: (output / "patches" / f"{name}.diff").read_text()
                                for name in ("upstream", "feature", "repair")}}
        write_json(output / "evidence.json", evidence)
        log.emit("explain", "Generating a four-scene explanation from the recorded evidence")
        try:
            story = model.generate(json.dumps(evidence), STORY_SCHEMA, "compose_storyboard", policy=
                "Write a concise developer explanation of this rebase in exactly four scenes: upstream change, "
                "feature assumption/failure, repair, verification. Each scene requires real evidence_ids from the bundle. "
                "Use a title under 70 characters and caption under 280 characters per scene, overall title under 90. "
                "Distinguish the scripted mechanical-control comparison from the actual agent's steps. Do not invent "
                "failures, test counts, performance metrics, or claim complete correctness. Explain causes as inferences "
                "from the included code diffs. State what moved or changed concretely. The controller ran the "
                "recorded checks; describe those results without discussing your own lack of tool execution. "
                "You generate the narrative; Manim renders it. No tools or file access are needed.")
            validate_story(story, evidence)
            state["story_status"] = "generated"
        except Exception as exc:
            state["story_status"] = "fallback"
            state["story_error"] = str(exc)
            story = {"title": "Your feature, brought forward", "scenes": [
                {"title": "Main moved forward", "caption": "Inspect the recorded upstream changes.", "evidence_ids": ["upstream"]},
                {"title": "Preserve the feature", "caption": state["intent"][:280], "evidence_ids": ["feature"]},
                {"title": "Review the adaptation", "caption": "Inspect the committed source repair.", "evidence_ids": ["repair"]},
                {"title": "Verification recorded", "caption": "Required checks passed on the committed candidate.", "evidence_ids": ["final-suite"]},
            ]}
        write_json(output / "storyboard.json", story)
        if render:
            from .render import render_video
            try:
                log.emit("render", "Rendering the evidence-backed Manim video")
                render_video(output)
                state["video_status"] = "rendered"
            except Exception as exc:
                state.update(video_status="failed", video_error=str(exc))
                log.emit("render", "Video render failed; the tested repair and written report remain available")
    except Exception as exc:
        if state["code_status"] == "running":
            state["code_status"] = "needs_review"
        state["error"] = str(exc)
        if "runner" in locals():
            state["checks"] = runner.checks
        log.emit("stopped", str(exc)[:500])
    finally:
        state["seconds"] = round(time.monotonic() - started, 2)
        write_json(output / "run.json", state)
        from .report import write_report
        log.emit("done", f"Code: {state['code_status']} · Video: {state['video_status']}")
        write_report(output)
    return state
