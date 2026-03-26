from PyQt6.QtWidgets import QTableWidgetItem


def get_last_valid_large_scale(table, break_col=0, sum_col=1):
    """
    Returns the most recent non-zero value in the Large Scale column.
    Stops when it hits an empty row in break_col.
    Returns 0.0 if no valid value is found.
    """
    for row in range(table.rowCount() - 1, -1, -1):
        # Stop at separator row
        break_item = table.item(row, break_col)
        if not break_item or not break_item.text().strip():
            break

        scale_item = table.item(row, sum_col)
        if not scale_item:
            continue

        try:
            if hasattr(scale_item, 'value'):
                value = float(scale_item.value)
            else:
                text = scale_item.text().replace(',', '').strip()
                value = float(text) if text else 0.0
        except (ValueError, TypeError):
            continue

        if value > 0.0:
            return value

    return 0.0


def handle_batch_break_manual(table, weight: float, batches: float = 1, limit: float = 25.0,
                              break_col: int = 0, sum_col: int = 1):
    """
    New logic:
    - Gets the last valid (non-zero) large scale
    - Calculates per_batch = weight / batches
    - If (last_valid + per_batch) > limit → insert empty break row
    """
    if weight <= 0 or batches <= 0:
        return False

    last_valid_scale = get_last_valid_large_scale(table, break_col, sum_col)
    per_batch = weight / batches

    total_to_check = last_valid_scale + per_batch

    if total_to_check > limit:
        row_pos = table.rowCount()
        table.insertRow(row_pos)

        # Insert empty separator row across all columns
        for col in range(table.columnCount()):
            table.setItem(row_pos, col, QTableWidgetItem(""))

        return True  # Break row was inserted

    return False     # No break needed