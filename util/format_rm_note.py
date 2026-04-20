import re

def get_bag_weight(text):
    """
    Extracts the first numeric weight (integer or decimal) found between 'x' and 'Kg'.
    Returns a string (e.g., "20" or "14.50") or None if not found.
    """
    if not text:
        return None

    # Pattern breakdown:
    # [xX]        : Matches lowercase 'x' or uppercase 'X'
    # \s*         : Matches 0 or more spaces
    # (\d*\.?\d+) : Capture group for the weight (handles '25', '14.50', or '.5')
    # \s*         : Matches 0 or more spaces
    # Kg          : Matches 'Kg'
    pattern = r'[xX]\s*(\d*\.?\d+)\s*Kg'

    # re.IGNORECASE makes it work for 'kg', 'KG', 'Kg', etc.
    # re.search finds the first occurrence
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        return match.group(1)

    return None
