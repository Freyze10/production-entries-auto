import re
from PyQt6.QtWidgets import QMessageBox

def validate_lot_field(parent, widget, existing_list, event,
                          title="PLEASE CHECK YOUR LOT NUMBER INPUT!",
                          msg_body="This value is already used.",
                          is_mb=True): # Added is_mb parameter
    """
    Generic validator for Lot Number patterns and duplicate checking.
    """
    raw_text = widget.text().strip().upper() # Standardize to uppercase for validation

    if not raw_text:
        return True

    # 1. --- Pattern Validation Logic ---
    if is_mb:
        # Pattern: 4 digits + 2 letters (e.g., 1212ZZ)
        pattern = r"^\d{4}[A-Z]{2}$"
        requirement = "FOUR DIGITS followed by TWO LETTERS (A~Z)"
    else:
        # Pattern: 4 digits + 1 letter (e.g., 1212Z)
        pattern = r"^\d{4}[A-Z]{1}$"
        requirement = "FOUR DIGITS followed by ONE CHARACTER (A~Z)"

    if not re.match(pattern, raw_text):
        QMessageBox.warning(
            parent,
            title,
            f"PLEASE CHECK LOT# {raw_text}.\n"
            f"NUMERIC VALUE MUST BE {requirement}.",
            QMessageBox.StandardButton.Ok
        )
        widget.setFocus()
        widget.selectAll()
        if event:
            event.ignore()
        return False

    check_value = raw_text.split('-', 1)[0].strip().upper()

    if check_value in existing_list:
        QMessageBox.warning(
            parent,
            "Duplicate Entry",
            f"{msg_body}\n\nValue: '{check_value}'",
            QMessageBox.StandardButton.Ok
        )
        widget.setFocus()
        widget.selectAll()
        if event:
            event.ignore()
        return False

    return True