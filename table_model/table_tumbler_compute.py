import math
from PyQt6.QtWidgets import QTableWidgetItem
from util.field_format import NumericTableWidgetItem
from util.format_rm_note import get_bag_limit


# Assuming get_bag_limit is imported from your logic file
# from logic.inventory import get_bag_limit

def compute_tumbler(source_table, target_table, total_weight, batch_divisor, base_divisor=100.0):
    """
    Calculates weights with dynamic physical scale limits (20kg or 25kg)
    based on the material code following a separator.
    """
    target_table.setRowCount(0)

    cumulative_raw = 0.0  # Running total for the Large Scale column
    running_physical_total = 0.0  # Tracker for the physical scale limit

    # --- NEW: Initialize dynamic limit ---
    # We look at the very first material to set the starting limit
    if source_table.rowCount() > 0:
        first_mat_code = source_table.item(0, 0).text().strip()
        current_limit = get_bag_limit(first_mat_code)
    else:
        current_limit = 25.0  # Fallback default

    # Factor to get total weight for the whole job
    factor = total_weight / base_divisor

    for row in range(source_table.rowCount()):
        mat_item = source_table.item(row, 0)
        con_item = source_table.item(row, 1)
        if not mat_item or not con_item: continue

        material_code = mat_item.text().strip()
        try:
            # Handle both custom NumericTableWidgetItem and standard QTableWidgetItem
            concentration = float(con_item.value) if hasattr(con_item, 'value') else float(con_item.text())
        except:
            concentration = 0.0

        # 1. Calculate Weights
        weight_total = factor * concentration
        weight_per_batch = weight_total / batch_divisor

        display_large_scale = 0.0
        display_small_scale = 0.0

        # 2. --- PRE-CHECK: SMALL MATERIAL TRANSFER ---
        if weight_per_batch <= 0.030 or weight_total < 0.10:
            display_large_scale = 0.0
            display_small_scale = weight_per_batch * 1000
        else:
            # 3. --- BULK MATERIAL ACCUMULATION ---

            # --- MODIFIED: Check for Batch Break using DYNAMIC current_limit ---
            if (running_physical_total + weight_per_batch) > current_limit:
                if target_table.rowCount() > 0:
                    sep_row = target_table.rowCount()
                    target_table.insertRow(sep_row)
                    for col in range(4):
                        target_table.setItem(sep_row, col, QTableWidgetItem(""))

                # --- NEW: Update the limit for the next section ---
                # The material that caused the break determines the limit for this new batch
                current_limit = get_bag_limit(material_code)

                # Reset totals for the new physical container
                running_physical_total = 0.0
                cumulative_raw = 0.0

            # Update Running Totals
            cumulative_raw += weight_per_batch
            running_physical_total += weight_per_batch

            # 4. --- GRAM STRIPPING LOGIC (POST-CUMULATIVE) ---
            safe_raw = round(cumulative_raw, 7)
            kilos_fixed = math.floor(round(safe_raw * 100, 1)) / 100.0
            gram_remainder_actual = round((safe_raw - kilos_fixed) * 1000, 4)

            if 0.000001 < gram_remainder_actual <= 30.0:
                display_large_scale = kilos_fixed
                display_small_scale = gram_remainder_actual
            else:
                display_large_scale = cumulative_raw
                display_small_scale = 0.0

            # Update the largescale cumulative value when the grams is separated
            cumulative_raw = display_large_scale

        # 5. Insert into Target Table
        row_pos = target_table.rowCount()
        target_table.insertRow(row_pos)
        target_table.setItem(row_pos, 0, QTableWidgetItem(material_code))
        target_table.setItem(row_pos, 1, NumericTableWidgetItem(display_large_scale, is_float=True))
        target_table.setItem(row_pos, 2, NumericTableWidgetItem(display_small_scale, is_float=True))
        target_table.setItem(row_pos, 3, NumericTableWidgetItem(weight_total, is_float=True))