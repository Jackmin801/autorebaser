"""Trusted demo evaluator. Runs outside the model's editable checkout."""
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile


def main():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        database = root / "bookmarks.db"
        records = [{"url": f"https://witness.example/{i}", "title": f"Independent record {i}"} for i in range(5)]
        filename = root / "records.json"
        filename.write_text(json.dumps(records))
        env = dict(os.environ, BOOKMARK_DB="sqlite:///" + str(database))
        result = subprocess.run([sys.executable, "-m", "app.cli", "import", str(filename)],
                                env=env, capture_output=True, text=True, timeout=20)
        if result.returncode:
            print(result.stderr)
            return 1
        with sqlite3.connect(database) as connection:
            rows = [dict(zip(("url", "title"), row)) for row in connection.execute("SELECT url, title FROM bookmarks ORDER BY url")]
        passed = rows == records
        print(json.dumps({"expected_count": len(records), "persisted_count": len(rows),
                          "exact_records_match": passed, "writer_stdout": result.stdout.strip()}))
        return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
