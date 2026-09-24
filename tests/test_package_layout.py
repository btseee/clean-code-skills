"""The scanner modules live in concept packages, not flat in the scripts folder.

detect_stack.py, scan_repo.py, check_boundaries.py, map_structure.py, and
check_compression.py are the only files a project runs directly; every other
module belongs to source, symbols, or structure. Each CLI must still work when
invoked as a script from outside the repository -- exactly how a project uses
it -- with its scripts folder on sys.path[0] the only reason `import symbols`
and `from source import files` resolve.
"""

import subprocess
import sys
import tempfile
import unittest

import support  # puts the scripts folder on sys.path

CLI_NAMES = ("detect_stack.py", "scan_repo.py", "check_boundaries.py", "map_structure.py",
             "check_compression.py")

# A representative set of standard-library top-level module names across Python
# 3.8-3.14, including names later versions removed (symbol, parser, cgi, ...).
# project_symbols.py once nearly became symbol.py, which would have shadowed this
# exact standard-library module; the package names chosen here must never repeat
# that mistake.
STDLIB_MODULE_NAMES = frozenset({
    "__future__", "_thread", "abc", "aifc", "argparse", "array", "ast", "asyncio",
    "atexit", "audioop", "base64", "bdb", "binascii", "binhex", "bisect", "builtins",
    "bz2", "calendar", "cgi", "cgitb", "chunk", "cmath", "cmd", "code", "codecs",
    "codeop", "collections", "colorsys", "compileall", "concurrent", "configparser",
    "contextlib", "contextvars", "copy", "copyreg", "cProfile", "crypt", "csv",
    "ctypes", "dataclasses", "datetime", "dbm", "decimal", "difflib", "dis",
    "distutils", "doctest", "email", "encodings", "ensurepip", "enum", "errno",
    "faulthandler", "fcntl", "filecmp", "fileinput", "fnmatch", "formatter",
    "fractions", "ftplib", "functools", "gc", "getopt", "getpass", "gettext",
    "glob", "graphlib", "grp", "gzip", "hashlib", "heapq", "hmac", "html", "http",
    "idlelib", "imaplib", "imghdr", "imp", "importlib", "inspect", "io",
    "ipaddress", "itertools", "json", "keyword", "lib2to3", "linecache",
    "locale", "logging", "lzma", "mailbox", "mailcap", "marshal", "math",
    "mimetypes", "mmap", "modulefinder", "msilib", "msvcrt", "multiprocessing",
    "netrc", "nis", "nntplib", "numbers", "operator", "optparse", "os",
    "ossaudiodev", "parser", "pathlib", "pdb", "pickle", "pickletools", "pipes",
    "pkgutil", "platform", "plistlib", "poplib", "posix", "posixpath", "pprint",
    "profile", "pstats", "pty", "pwd", "py_compile", "pyclbr", "pydoc", "queue",
    "quopri", "random", "re", "readline", "reprlib", "resource", "rlcompleter",
    "runpy", "sched", "secrets", "select", "selectors", "shelve", "shlex",
    "shutil", "signal", "site", "smtpd", "smtplib", "sndhdr", "socket",
    "socketserver", "spwd", "sqlite3", "sre_compile", "sre_constants",
    "sre_parse", "ssl", "stat", "statistics", "string", "stringprep", "struct",
    "subprocess", "sunau", "symbol", "symtable", "sys", "sysconfig", "syslog",
    "tabnanny", "tarfile", "telnetlib", "tempfile", "termios", "textwrap",
    "threading", "time", "timeit", "tkinter", "token", "tokenize", "tomllib",
    "trace", "traceback", "tracemalloc", "tty", "turtle", "turtledemo", "types",
    "typing", "unicodedata", "unittest", "urllib", "uu", "uuid", "venv",
    "warnings", "wave", "weakref", "webbrowser", "winreg", "winsound", "wsgiref",
    "xdrlib", "xml", "xmlrpc", "zipapp", "zipfile", "zipimport", "zlib",
    "zoneinfo",
})


class PackageLayoutTest(unittest.TestCase):
    def test_every_cli_runs_as_a_script_from_another_folder(self):
        for name in CLI_NAMES:
            with self.subTest(cli=name):
                with tempfile.TemporaryDirectory() as directory:
                    completed = subprocess.run(
                        [sys.executable, str(support.SCRIPTS_DIR / name), "--help"],
                        cwd=directory, capture_output=True, text=True, timeout=30,
                    )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn("usage:", completed.stdout)

    def test_library_modules_live_in_packages(self):
        top_level = {path.name for path in support.SCRIPTS_DIR.glob("*.py")}
        self.assertEqual(top_level, set(CLI_NAMES))
        for package in ("source", "symbols", "structure"):
            self.assertTrue(
                (support.SCRIPTS_DIR / package / "__init__.py").is_file(),
                f"{package}/__init__.py is missing")

    def test_no_package_shadows_the_standard_library(self):
        for name in ("symbol", "struct", "string", "symtable", "sre_parse"):
            self.assertIn(name, STDLIB_MODULE_NAMES)
        for package in ("source", "symbols", "structure"):
            self.assertNotIn(package, STDLIB_MODULE_NAMES)


if __name__ == "__main__":
    unittest.main()
