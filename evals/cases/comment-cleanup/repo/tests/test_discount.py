import unittest

from pricing.discount import apply_seasonal_discount


class DiscountTest(unittest.TestCase):
    def test_member_discount(self):
        self.assertEqual(apply_seasonal_discount(10000, True), 8500)

    def test_non_member_discount(self):
        self.assertEqual(apply_seasonal_discount(10000, False), 9000)
