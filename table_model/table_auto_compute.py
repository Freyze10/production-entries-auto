import math
from PyQt6.QtWidgets import QTableWidgetItem

from util.field_format import NumericTableWidgetItem


def process_formulation_to_table(source_table, target_table, total_weight, batch_divisor, base_divisor=100.0):
    """
    Calculates weights with dual-mode logic:
    1. Items <= 30g per batch go straight to Small Scale and don't affect Large Scale cumulative.
    2. Items > 30g are added to Large Scale cumulative with a 25kg break rule.
    3. Large Scale cumulative remainders <= 30g are stripped to Small Scale.
    """
    target_table.setRowCount(0)

    cumulative_raw = 0.0  # Running total for the Large Scale column
    running_physical_total = 0.0  # Tracker for the 25.0kg physical scale limit

    # Factor to get total weight for the whole job
    factor = total_weight / base_divisor

    for row in range(source_table.rowCount()):
        mat_item = source_table.item(row, 0)
        con_item = source_table.item(row, 1)
        if not mat_item or not con_item: continue

        material_code = mat_item.text().strip()
        try:
            concentration = float(con_item.value) if hasattr(con_item, 'value') else float(con_item.text())
        except:
            concentration = 0.0

        # 1. Calculate Weights
        # weight_total: Entire job weight | weight_per_batch: weight for one batch
        weight_total = factor * concentration
        weight_per_batch = weight_total / batch_divisor

        display_large_scale = 0.0
        display_small_scale = 0.0

        # 2. --- PRE-CHECK: SMALL MATERIAL TRANSFER ---
        # Requirement: If weight per batch <= 30g (0.030kg), put in Small Scale
        # and do NOT add to cumulative value.
        if weight_per_batch <= 0.030 or weight_total < 0.10:
            display_large_scale = 0.0
            display_small_scale = weight_per_batch * 1000  # Convert to grams
            # Skip the Large Scale accumulation logic for this row

        else:
            # 3. --- BULK MATERIAL ACCUMULATION ---

            # Check for 25.0kg Batch Break (Physical scale limit)
            if (running_physical_total + weight_per_batch) > 25.0:
                if target_table.rowCount() > 0:
                    sep_row = target_table.rowCount()
                    target_table.insertRow(sep_row)
                    for col in range(4):
                        target_table.setItem(sep_row, col, QTableWidgetItem(""))

                # Reset the scale totals for the new physical container/batch
                running_physical_total = 0.0
                cumulative_raw = 0.0

            # Update Running Totals
            cumulative_raw += weight_per_batch
            running_physical_total += weight_per_batch

            # 4. --- GRAM STRIPPING LOGIC (POST-CUMULATIVE) ---
            # Truncate to 2 decimal places to see what grams are "left over"
            safe_raw = round(cumulative_raw, 7)

            # FIX: Round the result of multiplication before flooring
            kilos_fixed = math.floor(round(safe_raw * 100, 1)) / 100.0

            # Calculate remainder in grams
            # We round this too, to prevent tiny errors like 7.169999999
            gram_remainder_actual = round((safe_raw - kilos_fixed) * 1000, 4)

            # Check thresholds: if the cumulative remainder is 30g or less
            if 0.000001 < gram_remainder_actual <= 30.0:
                display_large_scale = kilos_fixed
                display_small_scale = gram_remainder_actual
            else:
                display_large_scale = cumulative_raw
                display_small_scale = 0.0

        # 5. Insert into Target Table
        row_pos = target_table.rowCount()
        target_table.insertRow(row_pos)

        target_table.setItem(row_pos, 0, QTableWidgetItem(material_code))

        # Column 1: Large Scale (Kg)
        target_table.setItem(row_pos, 1, NumericTableWidgetItem(display_large_scale, is_float=True))

        # Column 2: Small Scale (grms)
        target_table.setItem(row_pos, 2, NumericTableWidgetItem(display_small_scale, is_float=True))

        # Column 3: Weight (Kg) - Per Batch weight for this material
        target_table.setItem(row_pos, 3, NumericTableWidgetItem(weight_total, is_float=True))