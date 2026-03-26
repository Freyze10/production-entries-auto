from PyQt6.QtWidgets import QTableWidgetItem


def get_batch_sum(table, break_col=0, sum_col=1):
    """
    Calculates the sum of values in a specific column since the last empty row.
    :param table: The QTableWidget to inspect.
    :param break_col: The column index used to identify empty/separator rows.
    :param sum_col: The column index containing the values to sum.
    """
    current_sum = 0.0
    # Iterate backwards through the provided table
    for row in range(table.rowCount() - 1, -1, -1):
        code_item = table.item(row, break_col)

        # Stop if we hit an empty row or a row with no data in the break column
        if not code_item or not code_item.text().strip():
            break

        # Get value from the sum column
        scale_item = table.item(row, sum_col)
        if scale_item:
            # Support both NumericTableWidgetItem (.value) and standard items (.text)
            if hasattr(scale_item, 'value'):
                val = float(scale_item.value)
            else:
                try:
                    text = scale_item.text().replace(',', '').strip()
                    val = float(text) if text else 0.0
                except ValueError:
                    val = 0.0
            current_sum += val

    return current_sum


def handle_batch_break_manual(table, new_value, limit=25.0, break_col=0, sum_col=1):
    """
    Inserts an empty row in the table if the limit is exceeded.
    :param table: The QTableWidget to modify.
    :param new_value: The numeric value currently being added.
    :param limit: The threshold for inserting a break (default 25.0).
    """
    current_batch_total = get_batch_sum(table, break_col, sum_col)

    if (current_batch_total + new_value) > limit:
        row_pos = table.rowCount()
        table.insertRow(row_pos)
        # Initialize empty items for all columns in the new row
        for col in range(table.columnCount()):
            table.setItem(row_pos, col, QTableWidgetItem(""))
        return True
    return False