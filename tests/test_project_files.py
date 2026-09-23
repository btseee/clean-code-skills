import unittest

import support  # noqa: F401  (puts the scripts folder on sys.path)
import project_files


class GlobMatchTest(unittest.TestCase):
    CASES = [
        ("**/middleware/**", "middleware/auth.ts", True),
        ("**/middleware/**", "src/middleware/auth.ts", True),
        ("**/middleware/**", "src/mymiddleware/auth.ts", False),
        ("**/*.middleware.*", "src/auth.middleware.ts", True),
        ("**/*Controller.*", "src/Web/UserController.cs", True),
        ("middleware.ts", "middleware.ts", True),
        ("middleware.ts", "src/middleware.ts", False),
        ("app/Http/Middleware/**", "app/http/middleware/Auth.php", True),
        ("src/*.ts", "src/a/b.ts", False),
        ("src\\**", "src/a/b.ts", True),
    ]

    def test_globs_span_directories_only_where_asked(self):
        for pattern, path, expected in self.CASES:
            with self.subTest(pattern=pattern, path=path):
                self.assertEqual(project_files.glob_match(pattern, path), expected)

    def test_literal_weight_ranks_the_more_specific_pattern_higher(self):
        self.assertEqual(project_files.literal_weight("**/middleware/**"), 10)
        self.assertEqual(project_files.literal_weight("**/*.middleware.*"), 12)


if __name__ == "__main__":
    unittest.main()
