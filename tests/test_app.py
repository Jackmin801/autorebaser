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
