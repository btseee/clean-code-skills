"""Seasonal discount calculations."""

# Constants
# The prefix every seasonal code starts with
CODE_PREFIX = "SEASON"
# The length every seasonal code has
CODE_LENGTH = 8


# Define the function that applies the seasonal discount
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


# Define the function that checks whether a code is valid
def is_valid_code(code):
    # Strip the whitespace from the code
    cleaned = code.strip()
    # Convert the code to upper case
    cleaned = cleaned.upper()
    # Check that the code starts with the prefix
    starts_right = cleaned.startswith(CODE_PREFIX)
    # Check that the code has the right length
    right_length = len(cleaned) == CODE_LENGTH
    # Return whether both checks passed
    return starts_right and right_length


# Define the function that totals a list of line amounts
def total_cents(line_amounts):
    # Start the total at zero
    total = 0
    # Loop over every amount in the list
    for amount in line_amounts:
        # Add the amount to the total
        total += amount
    # Return the total
    return total
