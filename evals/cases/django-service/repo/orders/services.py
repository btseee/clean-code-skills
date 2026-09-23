from .models import Order


def place_order(order: Order) -> None:
    order.status = "placed"
    order.save(update_fields=["status"])
