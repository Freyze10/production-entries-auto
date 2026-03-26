from PyQt6.QtWidgets import QTableWidgetItem


def get_last_valid_large_scale(table, break_col=0, sum_col=1):
    """Find the most recent non-zero Large Scale value from the bottom."""
    for row in range(table.rowCount() - 1, -1, -1):
        # Stop at separator/empty row
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


def handle_batch_break_manual(table, weight: float, batches: float = 1.0, limit: float = 25.0,
                              break_col: int = 0, sum_col: int = 1):
    """
    Checks if adding this weight (divided by batches) would exceed the limit.
    If yes → inserts an empty separator row.
    """
    if weight <= 0 or batches <= 0:
        return False

    last_valid = get_last_valid_large_scale(table, break_col, sum_col)
    per_batch = weight / batches

    if (last_valid + per_batch) > limit:
        row_pos = table.rowCount()
        table.insertRow(row_pos)

        # Insert empty row across all columns
        for col in range(table.columnCount()):
            table.setItem(row_pos, col, QTableWidgetItem(""))

        return True  # Break row was added

    return False