from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time


class RunError(RuntimeError):
    pass


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.replace(path)


def read_json(path: Path):
    return json.loads(path.read_text())


def digest(data: str | bytes) -> str:
    return hashlib.sha256(data.encode() if isinstance(data, str) else data).hexdigest()


def clean_env():
    keys = ("PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "SYSTEMROOT", "SSL_CERT_FILE")
    env = {k: os.environ[k] for k in keys if k in os.environ}
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONUNBUFFERED="1", GIT_TERMINAL_PROMPT="0",
               GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
               GIT_EDITOR="true", GIT_SEQUENCE_EDITOR="true",
               GIT_AUTHOR_NAME="Autorebaser", GIT_AUTHOR_EMAIL="bot@autorebaser.local",
               GIT_COMMITTER_NAME="Autorebaser", GIT_COMMITTER_EMAIL="bot@autorebaser.local")
    return env


def command(argv, cwd: Path, *, timeout=120, env=None, input_text=None, check=True):
    started = time.monotonic()
    proc = subprocess.Popen([str(a) for a in argv], cwd=cwd, env=env or clean_env(),
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, start_new_session=True)
    try:
        output, _ = proc.communicate(input_text, timeout=timeout)
        code = proc.returncode
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        output, _ = proc.communicate()
        code = 124
        output += f"\nCommand timed out after {timeout}s.\n"
    result = {"command": [str(a) for a in argv], "exit_code": code,
              "output": output, "seconds": round(time.monotonic() - started, 3)}
    if check and code:
        raise RunError(f"{' '.join(map(str, argv[:3]))} failed ({code}):\n{output[-5000:]}")
    return result


def git(repo: Path, *args, check=True):
    return command(["git", "-c", "core.hooksPath=/dev/null", *args], repo, check=check)


def git_text(repo: Path, *args):
    return git(repo, *args)["output"].strip()


def safe_file(root: Path, name: str):
    if not name or Path(name).is_absolute() or ".." in Path(name).parts:
        raise RunError(f"Invalid relative path: {name}")
    path = root / name
    if any(p.startswith(".") for p in Path(name).parts):
        raise RunError(f"Hidden paths are not editable: {name}")
    if not path.resolve().is_relative_to(root.resolve()):
        raise RunError(f"Path escapes checkout: {name}")
    if path.is_symlink():
        raise RunError(f"Symlinks are not supported: {name}")
    return path


class Journal:
    def __init__(self, directory: Path):
        self.directory = directory
        self.start = time.monotonic()

    def emit(self, stage: str, message: str, **data):
        event = {"stage": stage, "message": message,
                 "elapsed": round(time.monotonic() - self.start, 2), **data}
        with (self.directory / "events.jsonl").open("a") as handle:
            handle.write(json.dumps(event) + "\n")
        print(f"  [{event['elapsed']:6.1f}s] {stage:12} {message}", flush=True)
