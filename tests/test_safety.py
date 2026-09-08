import json
from pathlib import Path

import pytest

from autorebaser.core import patch, resolve, validate_story
from autorebaser.fixture import create_fixture
from autorebaser.util import RunError, git, git_text, safe_file


@pytest.fixture
def fixture_repo(tmp_path):
    path = tmp_path / "fixture"
    details = create_fixture(path)
    return path, details


def test_fixture_has_independent_linear_histories(fixture_repo):
    repo, refs = fixture_repo
    assert git_text(repo, "merge-base", refs["source"], refs["target"]) == refs["base"]
    assert git_text(repo, "rev-list", "--count", f"{refs['base']}..{refs['source']}") == "2"
    assert "1.4.54" in git_text(repo, "show", f"{refs['source']}:requirements.lock")
    assert "2.0.36" in git_text(repo, "show", f"{refs['target']}:requirements.lock")


def test_fixture_replays_cleanly_but_retains_old_feature_assumption(fixture_repo):
    repo, refs = fixture_repo
    git(repo, "checkout", "feature/bulk-import")
    git(repo, "rebase", "--onto", refs["target"], refs["base"])
    assert "from app.db import engine" in (repo / "app/importer.py").read_text()
    assert "engine.connect()" in (repo / "app/importer.py").read_text()
    assert "2.0.36" in (repo / "requirements.lock").read_text()


@pytest.mark.parametrize("name", ["../outside.py", "/tmp/outside.py", "app/../../outside.py", ".git/config"])
def test_path_escape_rejected(tmp_path, name):
    with pytest.raises(RunError):
        safe_file(tmp_path, name)


def test_symlink_escape_rejected(tmp_path):
    (tmp_path / "app").symlink_to(tmp_path.parent, target_is_directory=True)
    with pytest.raises(RunError):
        safe_file(tmp_path, "app/stolen.py")


@pytest.mark.parametrize("name", ["tests/test_app.py", "requirements.lock", "autorebaser.json", "app/tests/check.py"])
def test_protected_paths_cannot_be_patched(tmp_path, name):
    with pytest.raises(RunError):
        patch(tmp_path, {"changes": [{"path": name, "content": "x = 1"}]}, ["app/"])


def test_bad_patch_is_atomic(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app/a.py").write_text("original = True\n")
    proposal = {"changes": [{"path": "app/a.py", "content": "changed = True"},
                            {"path": "app/b.py", "content": "bad syntax !"}]}
    with pytest.raises(SyntaxError):
        patch(tmp_path, proposal, ["app/"])
    assert (tmp_path / "app/a.py").read_text() == "original = True\n"


def test_story_cannot_cite_nonexistent_evidence():
    story = {"title": "Example", "scenes": [{"title": "Scene", "caption": "Claim", "evidence_ids": ["invented-pass"]}] * 4}
    with pytest.raises(RunError, match="missing evidence"):
        validate_story(story, {"claims": [{"id": "real-check"}]})


def test_ref_option_injection_rejected(fixture_repo):
    with pytest.raises(RunError):
        resolve(fixture_repo[0], "--output=/tmp/example")
