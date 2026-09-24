"""Put the skill's scripts folder on the import path for every test module.

Run the suite from the repository root with:

    python -m unittest discover -s tests -v
"""

import contextlib
import io
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "clean-code"
SCRIPTS_DIR = SKILL_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def run_on_ansi_console(main, argv):
    """(exit code, output) of a script's main, run the way a pipe on Windows sees it.

    Such a stdout encodes in the ANSI code page, cp1252 here, which lacks most
    scripts; the output is decoded in whatever encoding the script left it.
    """
    buffer = io.BytesIO()
    console = io.TextIOWrapper(buffer, encoding="cp1252")
    with contextlib.redirect_stdout(console), contextlib.redirect_stderr(io.StringIO()):
        code = main(argv)
    console.flush()
    return code, buffer.getvalue().decode(console.encoding)
