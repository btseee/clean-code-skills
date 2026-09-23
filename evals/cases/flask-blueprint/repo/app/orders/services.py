_ORDERS = [
    {"id": 1, "month": "2026-01", "total_cents": 5000},
    {"id": 2, "month": "2026-01", "total_cents": 2500},
    {"id": 3, "month": "2026-02", "total_cents": 4000},
]


def list_orders() -> list[dict]:
    return _ORDERS
