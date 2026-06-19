"""
WSMIS Executive Chart Formatters
Global number formatting helpers for all WSMIS charts.

This module provides consistent Indian number formatting for
revenue, percentages, and other numeric values across all charts.
"""

from typing import Union


def fmt_inr_full(value: Union[int, float]) -> str:
    """
    Format value in Indian number system with full precision.
    
    Examples:
        12345678 -> "1,23,45,678"
        1234567 -> "12,34,567"
    
    Args:
        value: Numeric value to format
    
    Returns:
        Formatted string with Indian comma separators
    """
    if value is None or (isinstance(value, float) and (value != value)):  # NaN check
        return "—"
    
    try:
        value = float(value)
    except (ValueError, TypeError):
        return "—"
    
    # Convert to integer if it's a whole number
    if value == int(value):
        value = int(value)
    
    # Indian number system formatting
    s = str(abs(value))
    length = len(s)
    
    if length <= 3:
        return f"{'-' if value < 0 else ''}{s}"
    
    # Last 3 digits
    last_three = s[-3:]
    remaining = s[:-3]
    
    # Process remaining in groups of 2
    groups = []
    for i in range(len(remaining), 0, -2):
        start = max(0, i - 2)
        groups.insert(0, remaining[start:i])
    
    formatted = ",".join(groups) + "," + last_three
    return f"{'-' if value < 0 else ''}{formatted}"


def fmt_inr_short(value: Union[int, float]) -> str:
    """
    Format value in Indian number system with abbreviated units.
    
    Examples:
        10000000 -> "₹1.00 Cr"
        100000 -> "₹1.00 L"
        1000 -> "₹1,000"
    
    Args:
        value: Numeric value to format
    
    Returns:
        Formatted string with Indian units (Cr, L, K)
    """
    if value is None or (isinstance(value, float) and (value != value)):  # NaN check
        return "—"
    
    try:
        value = float(value)
    except (ValueError, TypeError):
        return "—"
    
    abs_val = abs(value)
    sign = "-" if value < 0 else ""
    
    # Crore (10 million)
    if abs_val >= 10000000:
        return f"{sign}₹{abs_val / 10000000:.2f} Cr"
    # Lakh (100 thousand)
    elif abs_val >= 100000:
        return f"{sign}₹{abs_val / 100000:.2f} L"
    # Thousand
    elif abs_val >= 1000:
        return f"{sign}₹{abs_val / 1000:.1f} K"
    # Less than 1000
    else:
        return f"{sign}₹{int(abs_val) if abs_val == int(abs_val) else abs_val:.0f}"


def fmt_pct(value: Union[int, float], sign: bool = False, decimals: int = 1) -> str:
    """
    Format value as percentage.
    
    Examples:
        0.172 -> "17.2%"
        -0.05 -> "-5.0%"
        0.172 with sign=True -> "+17.2%"
    
    Args:
        value: Numeric value (0.0 to 1.0 or already as percentage)
        sign: If True, prepend + for positive values
        decimals: Number of decimal places
    
    Returns:
        Formatted percentage string
    """
    if value is None or (isinstance(value, float) and (value != value)):  # NaN check
        return "—"
    
    try:
        value = float(value)
    except (ValueError, TypeError):
        return "—"
    
    # If value is > 1, assume it's already a percentage
    if abs(value) > 1:
        pct = value
    else:
        pct = value * 100
    
    formatted = f"{pct:.{decimals}f}%"
    
    if sign and pct > 0:
        formatted = f"+{formatted}"
    
    return formatted


def fmt_num(value: Union[int, float]) -> str:
    """
    Format value as plain number with commas (Western format for counts).
    
    Examples:
        1234567 -> "1,234,567"
        0 -> "0"
    
    Args:
        value: Numeric value to format
    
    Returns:
        Formatted string with Western comma separators
    """
    if value is None or (isinstance(value, float) and (value != value)):  # NaN check
        return "—"
    
    try:
        value = float(value)
    except (ValueError, TypeError):
        return "—"
    
    # Convert to integer if it's a whole number
    if value == int(value):
        value = int(value)
    
    return f"{value:,}"
