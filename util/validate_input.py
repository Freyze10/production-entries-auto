from PyQt6.QtWidgets import QMessageBox


def validate_lot_field(parent, widget, existing_list, event,
                          title="Duplicate Entry",
                          msg_body="This value is already used.",
                          transform_func=None):
    """
    Generic validator for QLineEdit focusOut events.
    """
    raw_text = widget.text().strip()

    if not raw_text:
        return True  # Valid because it's empty (allow leaving)

    # Use a custom transformation or the default 'lot' logic
    if transform_func:
        check_value = transform_func(raw_text)
    else:
        # Default: split by '-' and uppercase
        check_value = raw_text.split('-', 1)[0].strip().upper()

    if check_value in existing_list:
        QMessageBox.warning(
            parent,
            title,
            f"{msg_body}\n\nValue: '{check_value}'",
            QMessageBox.StandardButton.Ok
        )

        # Force focus back
        widget.setFocus()
        widget.selectAll()

        if event:
            event.ignore()
        return False

    return True