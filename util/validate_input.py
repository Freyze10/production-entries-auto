import re
from PyQt6.QtWidgets import QMessageBox

def validate_lot_field(parent, widget, existing_list, event,
                          title="PLEASE CHECK YOUR LOT NUMBER INPUT!",
                          msg_body="This value is already used.",
                          is_mb=True):
    """
    Validates Lot Numbers, supporting ranges (e.g., 6087AL-6088AL).
    Checks the first 6 chars for MB or first 5 chars for non-MB.
    """
    raw_text = widget.text().strip().upper()

    if not raw_text:
        return True

    # Split by '-' to handle ranges (e.g., '1212ZZ-1215ZZ' becomes ['1212ZZ', '1215ZZ'])
    # If there is no '-', it just creates a list with one item.
    lot_parts = [p.strip() for p in raw_text.split('-') if p.strip()]

    # Define validation rules
    check_len = 6 if is_mb else 5
    pattern = r"^\d{4}[A-Z]{2}$" if is_mb else r"^\d{4}[A-Z]{1}$"
    requirement = "4 DIGITS + 2 LETTERS" if is_mb else "4 DIGITS + 1 LETTER"

    for part in lot_parts:
        # Extract the prefix to validate (First 6 for MB, First 5 for Non-MB)
        # Note: If the part is shorter than check_len, prefix will just be the whole part
        prefix = part[:check_len]

        # 1. --- Pattern Validation for this part ---
        if not re.match(pattern, prefix):
            QMessageBox.warning(
                parent,
                title,
                f"INVALID FORMAT IN: '{part}'\n\n"
                f"The first {check_len} characters must be {requirement}.",
                QMessageBox.StandardButton.Ok
            )
            widget.setFocus()
            widget.selectAll()
            if event: event.ignore()
            return False

        # 2. --- Duplicate Check for this part ---
        # We check if the prefix (the specific lot) already exists in your expanded DB list
        if prefix in existing_list:
            QMessageBox.warning(
                parent,
                "Duplicate Entry",
                f"{msg_body}\n\nLot Number '{prefix}' already exists in records.",
                QMessageBox.StandardButton.Ok
            )
            widget.setFocus()
            widget.selectAll()
            if event: event.ignore()
            return False

    return True