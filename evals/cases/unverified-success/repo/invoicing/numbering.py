"""Sequential invoice numbering."""


def next_invoice_number(last_number):
    """The next invoice number after last_number, zero-padded to six digits."""
    return str(last_number + 1).zfill(5)
