"""Seasonal discount calculations."""


def apply_seasonal_discount(amount_cents, is_member):
    # Set the discount percent to 10
    discount_percent = 10
    # If the customer is a member
    if is_member:
        # Increase the discount percent by 5
        discount_percent += 5
    # Truncate rather than round: the payment processor already rounds the tax
    # component, and rounding here too would double-round and drift totals over time.
    return amount_cents * (100 - discount_percent) // 100
