import math
from PyQt6.QtWidgets import QTableWidgetItem
from util.field_format import NumericTableWidgetItem


def compute_generate(source_table, target_table, total_weight, batch_divisor, base_divisor=100.0):
    """
    Normal Generate Function:
    - Splits material rows if they exceed the 25kg limit.
    - Column 1: Cumulative Large Scale (capped at 25.0 per batch).
    - Column 2: Small Scale (remainders stripped from cumulative).
    - Column 3: Proportional total job weight for that slice.
    """
    target_table.setRowCount(0)
    cumulative_raw = 0.0  # Running total for the current batch
    running_physical_total = 0.0  # Tracks physical weight to trigger splits
    LIMIT = 25.0

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

        # Calculate per-batch requirement
        weight_total_full = factor * concentration
        weight_per_batch = weight_total_full / batch_divisor

        # --- CASE 1: SMALL MATERIAL (<= 30g) ---
        if weight_per_batch <= 0.030 or weight_total_full < 0.10:
            insert_production_row(target_table, material_code, 0.0, weight_per_batch * 1000, weight_total_full)
            continue

        # --- CASE 2: BULK MATERIAL (Potential Split) ---
        remaining_to_process = weight_per_batch

        while remaining_to_process > 0.0000001:
            space_left = LIMIT - running_physical_total

            # If no space left at all, insert break and reset
            if space_left <= 0:
                insert_separator(target_table)
                running_physical_total = 0.0
                cumulative_raw = 0.0
                space_left = LIMIT

            # Determine if we need to split this material
            if remaining_to_process > space_left:
                amount_for_this_row = space_left
                is_split_row = True
            else:
                amount_for_this_row = remaining_to_process
                is_split_row = False

            # Update Math
            cumulative_raw += amount_for_this_row
            running_physical_total += amount_for_this_row

            # Apply Gram Stripping to the cumulative result
            safe_raw = round(cumulative_raw, 7)
            kilos_fixed = math.floor(round(safe_raw * 100, 1)) / 100.0
            gram_remainder = round((safe_raw - kilos_fixed) * 1000, 4)

            if 0.000001 < gram_remainder <= 30.0:
                d_large, d_small = kilos_fixed, gram_remainder
            else:
                d_large, d_small = cumulative_raw, 0.0

            # Calculate the proportional "Weight" (Column 3) for this slice
            # Logic: (Amount added / Total per batch) * Total Job Weight
            slice_weight_total = (amount_for_this_row / weight_per_batch) * weight_total_full

            # Insert the row
            insert_production_row(target_table, material_code, d_large, d_small, slice_weight_total)

            # If we filled the batch exactly, add separator for the next loop/item
            if is_split_row:
                insert_separator(target_table)
                running_physical_total = 0.0
                cumulative_raw = 0.0
                remaining_to_process -= amount_for_this_row
            else:
                remaining_to_process = 0  # Finished this material


# --- HELPER FUNCTIONS ---

def insert_production_row(table, code, large, small, total):
    row_pos = table.rowCount()
    table.insertRow(row_pos)
    table.setItem(row_pos, 0, QTableWidgetItem(code))
    table.setItem(row_pos, 1, NumericTableWidgetItem(large, is_float=True))
    table.setItem(row_pos, 2, NumericTableWidgetItem(small, is_float=True))
    table.setItem(row_pos, 3, NumericTableWidgetItem(total, is_float=True))


def insert_separator(table):
    row_pos = table.rowCount()
    table.insertRow(row_pos)
    for col in range(4):
        table.setItem(row_pos, col, QTableWidgetItem(""))