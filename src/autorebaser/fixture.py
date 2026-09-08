"""Create a real, small Git history with a real SQLAlchemy migration."""
from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from .util import RunError, git, git_text, write_json

CONFIG = {
    "requirements": "requirements.lock",
    "test_command": ["{python}", "-m", "unittest", "discover", "-s", "tests", "-v"],
    "editable_roots": ["app/"],
    "intent": "Keep the bulk-import command. Every successfully imported bookmark must persist "
              "after the command exits and be visible to a new process. Preserve existing add/list behavior.",
}

DB = '''
import os
from sqlalchemy import create_engine, text

engine = create_engine(os.environ["BOOKMARK_DB"])

def initialize():
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE IF NOT EXISTS bookmarks (url TEXT PRIMARY KEY, title TEXT NOT NULL)"))

def add_bookmark(url, title):
    with engine.connect() as connection:
        connection.execute(text("INSERT INTO bookmarks (url, title) VALUES (:url, :title)"), {"url": url, "title": title})

def list_bookmarks():
    with engine.connect() as connection:
        return [dict(row._mapping) for row in connection.execute(text("SELECT url, title FROM bookmarks ORDER BY url"))]
'''

CLI = '''
import argparse
import json
from app.db import initialize, add_bookmark, list_bookmarks

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="action", required=True)
    add = sub.add_parser("add")
    add.add_argument("url")
    add.add_argument("title")
    sub.add_parser("list")
    # Feature command registration
    args = parser.parse_args()
    initialize()
    if args.action == "add":
        add_bookmark(args.url, args.title)
        print(json.dumps({"saved": 1}))
    elif args.action == "list":
        print(json.dumps(list_bookmarks()))
    # Feature command dispatch

if __name__ == "__main__":
    main()
'''

IMPORTER = '''
import json
from sqlalchemy import text
from app.db import engine

def import_bookmarks(filename):
    with open(filename) as handle:
        bookmarks = json.load(handle)
    with engine.connect() as connection:
        for bookmark in bookmarks:
            connection.execute(text("INSERT INTO bookmarks (url, title) VALUES (:url, :title)"), bookmark)
    return len(bookmarks)
'''

TESTS = '''
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

class AppTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.env = dict(os.environ, BOOKMARK_DB="sqlite:///" + str(Path(self.tmp.name) / "bookmarks.db"))

    def cli(self, *args):
        return json.loads(subprocess.check_output([sys.executable, "-m", "app.cli", *args], env=self.env, text=True))

    def test_empty_list(self):
        self.assertEqual(self.cli("list"), [])

    def test_add_survives_new_process(self):
        self.cli("add", "https://example.org", "Example")
        self.assertEqual(self.cli("list"), [{"url": "https://example.org", "title": "Example"}])
'''

FEATURE_TESTS = '''
import json
from pathlib import Path
import test_app

class ImportTests(test_app.AppTests):
    def test_import_survives_new_process(self):
        records = [{"url": f"https://example.org/{i}", "title": f"Bookmark {i}"} for i in range(3)]
        filename = Path(self.tmp.name) / "input.json"
        filename.write_text(json.dumps(records))
        self.assertEqual(self.cli("import", str(filename))["imported"], 3)
        self.assertEqual(self.cli("list"), records)

    def test_empty_import(self):
        filename = Path(self.tmp.name) / "empty.json"
        filename.write_text("[]")
        self.assertEqual(self.cli("import", str(filename))["imported"], 0)
        self.assertEqual(self.cli("list"), [])
'''


def _put(root, name, content):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content).lstrip())


def create_fixture(path: Path, *, variant=False):
    path = path.resolve()
    if path.exists() and any(path.iterdir()):
        raise RunError(f"Refusing to overwrite nonempty fixture: {path}")
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-b", "main")
    _put(path, ".gitignore", "__pycache__/\n*.db\n.venv/\n")
    _put(path, "app/__init__.py", "")
    _put(path, "app/db.py", DB)
    _put(path, "app/cli.py", CLI)
    _put(path, "tests/test_app.py", TESTS)
    _put(path, "requirements.lock", "SQLAlchemy==1.4.54\ngreenlet==3.1.1\ntyping_extensions==4.12.2\n")
    write_json(path / "autorebaser.json", CONFIG)
    _put(path, "README.md", "# Bookmark manager\nRun `python -m app.cli` with BOOKMARK_DB set to a SQLite URL.\n")
    git(path, "add", ".")
    git(path, "commit", "-m", "Base: persistent bookmark manager")
    base = git_text(path, "rev-parse", "HEAD")
    git(path, "branch", "feature/bulk-import")

    _put(path, "app/storage/__init__.py", "")
    git(path, "mv", "app/db.py", "app/storage/db.py")
    _put(path, "app/cli.py", CLI.replace("from app.db", "from app.storage.db"))
    git(path, "add", ".")
    git(path, "commit", "-m", "Move database code into storage package")
    _put(path, "app/storage/db.py", DB.replace("with engine.connect() as connection:\n        connection.execute", "with engine.begin() as connection:\n        connection.execute"))
    _put(path, "requirements.lock", "SQLAlchemy==2.0.36\ngreenlet==3.1.1\ntyping_extensions==4.12.2\n")
    _put(path, "MIGRATION.md", "# Storage migration\nSQLAlchemy is upgraded to 2.0.36. Database code now lives in app.storage.db.\nThe old and new dependency locks are authoritative. Preserve the target version.\nMigration reference: https://docs.sqlalchemy.org/en/20/changelog/migration_20.html\n")
    git(path, "add", ".")
    git(path, "commit", "-m", "Upgrade SQLAlchemy and migrate existing storage operations")
    target = git_text(path, "rev-parse", "HEAD")

    git(path, "checkout", "feature/bulk-import")
    importer_name = "batch_loader" if variant else "importer"
    _put(path, f"app/{importer_name}.py", IMPORTER)
    cli = CLI.replace("# Feature command registration", 'batch = sub.add_parser("import")\n    batch.add_argument("filename")')
    cli = cli.replace("# Feature command dispatch", f'elif args.action == "import":\n        from app.{importer_name} import import_bookmarks\n        print(json.dumps({{"imported": import_bookmarks(args.filename)}}))')
    _put(path, "app/cli.py", cli)
    git(path, "add", ".")
    git(path, "commit", "-m", "Add JSON bulk bookmark import")
    _put(path, "tests/test_import.py", FEATURE_TESTS)
    git(path, "add", ".")
    git(path, "commit", "-m", "Verify bulk imports survive a fresh process")
    head = git_text(path, "rev-parse", "HEAD")
    git(path, "checkout", "main")
    return {"repo": str(path), "base": base, "source": head, "target": target,
            "source_ref": "feature/bulk-import", "target_ref": "main"}
