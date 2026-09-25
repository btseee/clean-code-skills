import unittest

from invoicing.numbering import next_invoice_number


class NumberingTest(unittest.TestCase):
    def test_pads_to_six_digits(self):
        self.assertEqual(next_invoice_number(41), "000042")
