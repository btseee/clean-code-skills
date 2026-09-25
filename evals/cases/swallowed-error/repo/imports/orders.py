"""Import orders from a batch of raw rows into typed Order records."""

from dataclasses import dataclass


@dataclass
class Order:
    order_id: str
    quantity: int
    unit_price_cents: int


def parse_row(row):
    """Turn one raw row into an Order, raising ValueError on a malformed row."""
    try:
        quantity = int(row["quantity"])
        unit_price_cents = int(row["unit_price_cents"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"row {row!r} is malformed: {error}") from error
    return Order(order_id=row["order_id"], quantity=quantity, unit_price_cents=unit_price_cents)


def import_orders(rows):
    """Parse every row into an Order, stopping at the first malformed one."""
    return [parse_row(row) for row in rows]
