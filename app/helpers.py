def format_naira(amount):
    """Format amount as Nigerian Naira"""
    if amount is None:
        return "₦0.00"

    try:
        amount = float(amount)
        return f"₦{amount:,.2f}"
    except (ValueError, TypeError):
        return "₦0.00"


def format_number(num):
    """Format number with commas"""
    if num is None:
        return "0"

    try:
        num = float(num)
        return f"{num:,.0f}"
    except (ValueError, TypeError):
        return "0"