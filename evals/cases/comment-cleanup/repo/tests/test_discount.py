import unittest

from pricing.discount import apply_seasonal_discount, is_valid_code, total_cents


class DiscountTest(unittest.TestCase):
    def test_member_discount(self):
        self.assertEqual(apply_seasonal_discount(10000, True), 8500)

    def test_non_member_discount(self):
        self.assertEqual(apply_seasonal_discount(10000, False), 9000)

    def test_discount_truncates(self):
        self.assertEqual(apply_seasonal_discount(999, False), 899)


class CodeTest(unittest.TestCase):
    def test_a_seasonal_code_is_valid_in_any_case(self):
        self.assertTrue(is_valid_code(" season24 "))

    def test_a_code_of_the_wrong_length_is_invalid(self):
        self.assertFalse(is_valid_code("SEASON2024"))

    def test_a_code_with_another_prefix_is_invalid(self):
        self.assertFalse(is_valid_code("SUMMER24"))


class TotalTest(unittest.TestCase):
    def test_total_adds_every_line(self):
        self.assertEqual(total_cents([100, 250, 5]), 355)

    def test_total_of_no_lines_is_zero(self):
        self.assertEqual(total_cents([]), 0)
