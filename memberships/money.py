def format_inr(amount):
    """Format a whole-rupee amount with Indian digit grouping."""
    value = int(amount)
    sign = "-" if value < 0 else ""
    digits = str(abs(value))
    if len(digits) <= 3:
        grouped = digits
    else:
        grouped = digits[-3:]
        digits = digits[:-3]
        while digits:
            grouped = digits[-2:] + "," + grouped
            digits = digits[:-2]
    return f"{sign}₹{grouped}"
