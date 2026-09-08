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
