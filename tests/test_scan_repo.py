import json
import tempfile
import unittest
from pathlib import Path

import support  # puts the scripts folder on sys.path
import scan_repo


class ConsoleTest(unittest.TestCase):
    def test_json_reaches_a_console_that_cannot_encode_the_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "项目"
            (root / "src").mkdir(parents=True)
            (root / "src" / "app.py").write_text("def main():\n    return 1\n", encoding="utf-8")
            code, output = support.run_on_ansi_console(scan_repo.main, ["--root", str(root), "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(Path(json.loads(output)["root"]).name, "项目")


if __name__ == "__main__":
    unittest.main()
