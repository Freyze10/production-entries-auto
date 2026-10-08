import re

from db.read import get_material_note


def get_bag_weight(text):
    """
    Extracts the first numeric weight (integer or decimal) found between 'x' and 'Kg'.
    """
    if not text:
        return None

    pattern = r'[xX]\s*(\d*\.?\d+)\s*Kg'
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        return match.group(1)
    return None


def get_bag_limit(material_code):
    # 1. Get the raw text note from the database
    text_output = get_material_note(material_code)

    # 2. Extract the weight string (e.g., "25" or "14.50")
    weight_str = get_bag_weight(text_output)

    # 3. If a weight was found, convert to number and apply logic
    if weight_str:
        try:
            weight_num = float(weight_str)

            if weight_num > 20:
                return 25
            else:
                return 20  # +1kg para sa allowance weight depends kung kasya pa
        except ValueError:
            # In case the string can't be converted to a float
            return 25

            # 4. Default return value if no weight is found in the text
    return 25
