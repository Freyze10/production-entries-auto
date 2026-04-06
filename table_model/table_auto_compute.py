from PyQt6.QtWidgets import QTableWidgetItem

from util.field_format import NumericTableWidgetItem


def process_formulation_to_table(self, source_table, target_table, total_weight, batch_divisor, base_divisor=100.0):
    """
    source_table: self.formulation_details (Material, Concentration)
    target_table: The table to insert into (Material, Large Scale, Small Scale, Weight)
    total_weight: The total weight value to calculate against.
    batch_divisor: The batch quantity to divide the weight by.
    base_divisor: Default is 100.0 as requested.
    """
    # 1. Clear target table before starting
    target_table.setRowCount(0)

    # Tracking variables
    cumulative_large_scale = 0.0  # The "Running Total" for Large Scale column
    running_batch_total = 0.0  # For the 25.0kg Batch Break logic

    # Calculate the constant factor
    factor = total_weight / base_divisor

    for row in range(source_table.rowCount()):
        # Get Material Code (Col 0)
        mat_item = source_table.item(row, 0)
        if not mat_item or not mat_item.text().strip():
            continue
        material_code = mat_item.text().strip()

        # Get Concentration (Col 1)
        con_item = source_table.item(row, 1)
        try:
            # Handle both NumericTableWidgetItem (.value) and standard items (.text)
            concentration = float(con_item.value) if hasattr(con_item, 'value') else float(con_item.text())
        except (ValueError, TypeError, AttributeError):
            concentration = 0.0

        # --- CALCULATIONS ---

        # Calculate Weight: (Total Weight / 100) * Concentration
        calculated_weight = factor * concentration

        small_scale = 0.0
        large_scale_to_add = 0.0

        if calculated_weight < 0.10:
            # Logic: If < 0.10, convert to grams (Small Scale)
            small_scale = calculated_weight * 1000
            # Cumulative large scale does not change for small scale items
        else:
            # Logic: (Weight / Batch) + Previous Cumulative Large Scale
            large_scale_to_add = calculated_weight / batch_divisor

            # --- BATCH BREAK LOGIC (25.0 Rule) ---
            # Check if adding this material pushes the PHYSICAL scale over 25kg
            if (running_batch_total + large_scale_to_add) > 25.0:
                # Insert Empty Separator Row
                sep_row = target_table.rowCount()
                target_table.insertRow(sep_row)
                for col in range(target_table.columnCount()):
                    target_table.setItem(sep_row, col, QTableWidgetItem(""))

                # Reset physical scale total for the new batch
                running_batch_total = 0.0

            # Update tracking variables
            running_batch_total += large_scale_to_add
            cumulative_large_scale += large_scale_to_add

        # Final display value for large scale column
        # If it was a small scale item, we usually show 0 or the current cumulative
        display_large_scale = cumulative_large_scale if calculated_weight >= 0.10 else 0.0

        # --- INSERT INTO TARGET TABLE ---
        row_pos = target_table.rowCount()
        target_table.insertRow(row_pos)

        target_table.setItem(row_pos, 0, QTableWidgetItem(material_code))
        # Use NumericTableWidgetItem (assuming you use this class for alignment/formatting)
        target_table.setItem(row_pos, 1, NumericTableWidgetItem(display_large_scale, is_float=True))
        target_table.setItem(row_pos, 2, NumericTableWidgetItem(small_scale, is_float=True))
        target_table.setItem(row_pos, 3, NumericTableWidgetItem(calculated_weight, is_float=True))

    # Update totals at the end (using your previous function)
    if hasattr(self, 'update_totals'):
        self.update_totals()

