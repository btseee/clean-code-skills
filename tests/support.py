"""Put the skill's scripts folder on the import path for every test module.

Run the suite from the repository root with:

    python -m unittest discover -s tests -v
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "clean-code"
SCRIPTS_DIR = SKILL_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
