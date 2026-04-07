import math
from PyQt6.QtWidgets import QTableWidgetItem

from util.field_format import NumericTableWidgetItem


def process_formulation_to_table(self, source_table, target_table, total_weight, batch_divisor, base_divisor=100.0):
    """
    Calculates cumulative Large Scale weight and strips small gram remainders 
    (<= 30g or <= 9g) to the Small Scale column.
    """
    target_table.setRowCount(0)

    cumulative_raw = 0.0  # Running total for math
    running_physical_total = 0.0  # Tracker for the 25.0kg scale limit

    # Factor to get total weight for the whole job
    factor = total_weight / base_divisor

    for row in range(source_table.rowCount()):
        # 1. Get Material and Concentration
        mat_item = source_table.item(row, 0)
        con_item = source_table.item(row, 1)
        if not mat_item or not con_item: continue

        material_code = mat_item.text().strip()
        try:
            concentration = float(con_item.value) if hasattr(con_item, 'value') else float(con_item.text())
        except:
            concentration = 0.0

        # 2. Calculate Weight per batch
        # This is the actual physical weight of this specific line item for ONE batch
        weight_per_batch = (factor * concentration) / batch_divisor

        # 3. Check for 25.0kg Batch Break
        # If adding this weight exceeds 25kg on the physical scale, we start a new batch
        if (running_physical_total + weight_per_batch) > 25.0:
            sep_row = target_table.rowCount()
            target_table.insertRow(sep_row)
            for col in range(4):
                target_table.setItem(sep_row, col, QTableWidgetItem(""))

            # Reset the scale totals for the new physical batch/bag
            running_physical_total = 0.0
            cumulative_raw = 0.0

        # 4. Update Running Totals
        cumulative_raw += weight_per_batch
        running_physical_total += cumulative_raw

        # 5. --- GRAM STRIPPING LOGIC (POST-CUMULATIVE) ---
        # We look at the 3rd decimal place and beyond
        # To get the remainder below 0.010 (two decimal places), we truncate to 2 decimals
        kilos_fixed = math.floor(cumulative_raw * 100) / 100.0
        gram_remainder_kg = cumulative_raw - kilos_fixed
        gram_remainder_actual = gram_remainder_kg * 1000  # Convert to actual grams

        display_large_scale = 0.0
        display_small_scale = 0.0

        # Check thresholds: if the remainder is 30g or less (which covers 9g or less)
        if 0.000001 < gram_remainder_actual <= 30.0:
            # Strip the grams: Large Scale gets the truncated Kilos
            display_large_scale = kilos_fixed
            # Small Scale gets the stripped grams
            display_small_scale = gram_remainder_actual
        else:
            # Keep it all in Large Scale
            display_large_scale = cumulative_raw
            display_small_scale = 0.0

        # 6. Insert into Target Table
        row_pos = target_table.rowCount()
        target_table.insertRow(row_pos)

        target_table.setItem(row_pos, 0, QTableWidgetItem(material_code))

        # Column 1: Large Scale (Kg) - Stripped of small remainders
        target_table.setItem(row_pos, 1, NumericTableWidgetItem(display_large_scale, is_float=True))

        # Column 2: Small Scale (grms) - Receives the stripped remainders
        target_table.setItem(row_pos, 2, NumericTableWidgetItem(display_small_scale, is_float=True))

        # Column 3: Weight (Kg) - Always the raw calculated weight per batch
        target_table.setItem(row_pos, 3, NumericTableWidgetItem(weight_per_batch, is_float=True))

    # Update UI totals
    if hasattr(self, 'update_totals'):
        self.update_totals()