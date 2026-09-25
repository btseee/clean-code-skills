import unittest

from imports.orders import Order, import_orders


class ImportOrdersTest(unittest.TestCase):
    def test_imports_well_formed_rows(self):
        rows = [
            {"order_id": "A1", "quantity": "2", "unit_price_cents": "500"},
            {"order_id": "A2", "quantity": "1", "unit_price_cents": "1200"},
        ]
        self.assertEqual(
            import_orders(rows),
            [Order("A1", 2, 500), Order("A2", 1, 1200)],
        )
