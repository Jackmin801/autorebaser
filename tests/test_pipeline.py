import json
import os

import pytest

from autorebaser import core
from autorebaser.fixture import create_fixture
from autorebaser.publish import publish
from autorebaser.runner import Runner
from autorebaser.util import RunError, clean_env, git, git_text, read_json, write_json


def test_failed_baseline_stops_before_inference(tmp_path, monkeypatch):
    repo = tmp_path / "fixture"
    create_fixture(repo)

    class FailedRunner:
        def __init__(self, *args):
            self.checks = []

        def check(self, *args, **kwargs):
            return [{"passed": False}]

    class NoInference:
        provider, model = "test", "test"

        def __init__(self, *args):
            pass

        def generate(self, *args):
            pytest.fail("A failed baseline must stop before model inference")

    monkeypatch.setattr(core, "Runner", FailedRunner)
    monkeypatch.setattr(core, "Model", NoInference)
    result = core.run_rebase(str(repo), "feature/bulk-import", "main", tmp_path / "failed", render=False)
    assert result["code_status"] == "baseline_failed"
    assert "candidate" not in result
    assert not result["repairs"]


def test_test_environment_omits_credentials(monkeypatch):
    for name in ("OPENAI_API_KEY", "GH_TOKEN", "GITHUB_TOKEN", "AWS_SECRET_ACCESS_KEY"):
        monkeypatch.setenv(name, "test-secret")
        assert name not in clean_env()


def test_stale_inputs_never_push(tmp_path, monkeypatch):
    import autorebaser.publish as module
    write_json(tmp_path / "run.json", {"code_status": "passed", "target_ref": "main", "source_ref": "feature",
        "target": "a" * 40, "source": "b" * 40, "candidate": "c" * 40, "branch": "codex/repaired"})
    calls = []

    def remote_refs(argv, *args, **kwargs):
        calls.append(argv)
        assert argv[:2] == ["git", "ls-remote"]
        return {"output": f"{'d' * 40}\trefs/heads/main\n{'b' * 40}\trefs/heads/feature\n"}

    monkeypatch.setattr(module, "command", remote_refs)
    monkeypatch.setattr(module, "write_report", lambda _: None)
    with pytest.raises(RunError, match="fresh run"):
        publish(tmp_path, "owner/repository")
    assert len(calls) == 1
    assert read_json(tmp_path / "run.json")["publication_status"] == "stale"


def test_unvalidated_candidate_cannot_publish(tmp_path):
    write_json(tmp_path / "run.json", {"code_status": "needs_review"})
    with pytest.raises(RunError, match="validated"):
        publish(tmp_path, "owner/repository")


@pytest.mark.skipif(os.getenv("AUTOREBASER_TEST_DOCKER") != "1", reason="Docker integration runs in CI")
def test_docker_detects_and_verifies_transaction_regression(tmp_path):
    repo = tmp_path / "fixture"
    refs = create_fixture(repo)
    config = json.loads(git_text(repo, "show", f"{refs['target']}:autorebaser.json"))
    output = tmp_path / "checks"
    output.mkdir()
    runner = Runner(output, config, "docker")
    git(repo, "checkout", "feature/bulk-import")
    assert all(c["passed"] for c in runner.check(repo, "original", refs["source"], witness=True))
    git(repo, "rebase", "--onto", refs["target"], refs["base"])
    importer = repo / "app/importer.py"
    importer.write_text(importer.read_text().replace("from app.db import", "from app.storage.db import"))
    broken = runner.check(repo, "control", git_text(repo, "rev-parse", "HEAD"), witness=True)
    assert not any(c["passed"] for c in broken)
    assert '"persisted_count": 0' in broken[1]["output"]
    importer.write_text(importer.read_text().replace("engine.connect()", "engine.begin()"))
    fixed = runner.check(repo, "fixed", git_text(repo, "rev-parse", "HEAD"), witness=True)
    assert all(c["passed"] for c in fixed)
    assert '"persisted_count": 5' in fixed[1]["output"]
