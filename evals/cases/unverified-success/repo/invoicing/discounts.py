"""Discount calculations for invoicing."""


def apply_flat_discount(amount_cents, discount_cents):
    """Reduce amount_cents by a flat discount, never going below zero."""
    return max(0, amount_cents - discount_cents)
