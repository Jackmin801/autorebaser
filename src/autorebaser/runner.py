from __future__ import annotations

from pathlib import Path
import re
import shutil
import sys

from . import probe
from .util import RunError, clean_env, command, digest, write_json


class Runner:
    def __init__(self, directory: Path, config: dict, executor: str):
        self.directory, self.config, self.executor = directory, config, executor
        self.cache = directory / "environments"
        self.cache.mkdir()
        self.trusted = directory / "trusted"
        self.trusted.mkdir()
        shutil.copyfile(probe.__file__, self.trusted / "probe.py")
        self.prepared = {}
        self.checks = []

    def prepare(self, repo: Path):
        requirements = repo / self.config["requirements"]
        content = requirements.read_text()
        # The first version supports exact registry pins only, no VCS URLs or pip directives.
        if not content.strip() or any(not re.fullmatch(r"[\w.\-]+==[\w.+\-]+", line.strip())
                                      for line in content.splitlines() if line.strip()):
            raise RunError("Requirements must contain exact package==version pins only")
        fingerprint = digest(content + sys.version + self.executor)
        environment = self.cache / fingerprint[:16]
        if fingerprint not in self.prepared:
            env = clean_env()
            env["UV_CACHE_DIR"] = str(self.directory / "uv-cache")
            if self.executor == "local":
                command(["uv", "venv", "--python", sys.executable, environment], repo, env=env)
                python = environment / "bin/python"
                result = command(["uv", "pip", "install", "--python", python, "-r", requirements],
                                 repo, timeout=180, env=env)
                versions = command(["uv", "pip", "freeze", "--python", python], repo, env=env)["output"]
            else:
                environment.mkdir()
                result = command(["docker", "run", "--rm", "-v", f"{repo}:/workspace:ro",
                                  "-v", f"{environment}:/deps", "python:3.12-slim",
                                  "pip", "install", "--target", "/deps", "-r",
                                  f"/workspace/{self.config['requirements']}"], repo, timeout=240)
                versions = content
            write_json(environment / "installation.json", result)
            self.prepared[fingerprint] = {"path": str(environment), "fingerprint": fingerprint,
                                          "requirements": content, "installed": versions,
                                          "executor": self.executor}
            write_json(self.directory / "environments.json", list(self.prepared.values()))
        return environment, fingerprint

    def check(self, repo: Path, label: str, sha: str, *, witness=False):
        environment, fingerprint = self.prepare(repo)
        commands = [("suite", self.config["test_command"])]
        if witness:
            commands.append(("persistence", ["{python}", "{probe}"]))
        observed = []
        for kind, argv in commands:
            python = str(environment / "bin/python") if self.executor == "local" else "python"
            probe_path = str(self.trusted / "probe.py") if self.executor == "local" else "/trusted/probe.py"
            expanded = [a.replace("{python}", python).replace("{probe}", probe_path) for a in argv]
            env = clean_env()
            if self.executor == "docker":
                expanded = ["docker", "run", "--rm", "--network", "none", "--read-only",
                            "--cap-drop=ALL", "--security-opt=no-new-privileges", "--pids-limit=128",
                            "--memory=1g", "--cpus=2", "--tmpfs", "/tmp:rw,size=256m",
                            "-v", f"{repo}:/workspace:ro", "-v", f"{environment}:/deps:ro",
                            "-v", f"{self.trusted}:/trusted:ro", "-w", "/workspace",
                            "-e", "PYTHONPATH=/deps:/workspace", "-e", "PYTHONDONTWRITEBYTECODE=1",
                            "python:3.12-slim", *expanded]
            else:
                env["PYTHONPATH"] = str(repo)
            result = command(expanded, repo, timeout=90, env=env, check=False)
            item = {"id": f"{label}-{kind}", "label": label, "kind": kind, "sha": sha,
                    "environment": fingerprint, "passed": result["exit_code"] == 0, **result}
            match = re.search(r"Ran (\d+) tests?", result["output"])
            item["test_count"] = int(match.group(1)) if match else None
            if kind == "suite" and ("unittest" in argv) and (not match or int(match.group(1)) == 0):
                item["passed"] = False
                item["output"] += "\nRequired unittest suite did not report any executed tests.\n"
            self.checks.append(item)
            observed.append(item)
            write_json(self.directory / "checks" / (item["id"] + ".json"), item)
            (self.directory / "checks" / (item["id"] + ".log")).write_text(item["output"])
        return observed
