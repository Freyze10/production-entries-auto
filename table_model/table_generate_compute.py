import math
from PyQt6.QtWidgets import QTableWidgetItem
from util.field_format import NumericTableWidgetItem


def compute_generate(source_table, target_table, total_weight, batch_divisor, base_divisor=100.0):
    """
    Normal Generate Function with Priority Splitting:
    - If a material is > 25kg, it resets the current batch (blank row) if needed.
    - Slices the material into a 25.0kg row, then a blank row, then the remainder.
    """
    target_table.setRowCount(0)
    cumulative_raw = 0.0  # Running total for the Large Scale column
    running_physical_total = 0.0  # Tracker for the 25.0kg physical container limit
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

        # Calculate per-batch weights
        weight_total_full = factor * concentration
        weight_per_batch = weight_total_full / batch_divisor

        # --- CASE 1: SMALL MATERIAL (<= 30g) ---
        if weight_per_batch <= 0.030 or weight_total_full < 0.10:
            insert_production_row(target_table, material_code, 0.0, weight_per_batch * 1000, weight_per_batch)
            continue

        # --- CASE 2: BIG MATERIAL SPLITTING (> 25kg) ---
        if weight_per_batch > LIMIT:
            # Requirement: If there is already a value in Large Scale, add empty row before splitting
            if running_physical_total > 0:
                insert_separator(target_table)
                running_physical_total = 0.0
                cumulative_raw = 0.0

            remaining_item_weight = weight_per_batch

            while remaining_item_weight > LIMIT:
                # Calculate proportional weight for the 25kg slice
                slice_total = (LIMIT / weight_per_batch) * weight_total_full

                # Insert the exactly 25.0kg row
                insert_production_row(target_table, material_code, LIMIT, 0.0, slice_total)

                # After a 25kg row, we always add a separator
                insert_separator(target_table)

                remaining_item_weight -= LIMIT
                running_physical_total = 0.0
                cumulative_raw = 0.0

            # Now we treat the remainder (e.g. 0.30kg) as a normal item for the next steps
            # We must also adjust the weight_total_full for the remainder row
            weight_total_full = (remaining_item_weight / weight_per_batch) * weight_total_full
            weight_per_batch = remaining_item_weight

        # --- CASE 3: NORMAL MATERIAL (OR REMAINDER OF SPLIT) ---
        # Check if adding this pushes the current container over 25kg
        if (running_physical_total + weight_per_batch) > LIMIT:
            if target_table.rowCount() > 0:
                insert_separator(target_table)
            running_physical_total = 0.0
            cumulative_raw = 0.0

        # Update Math
        cumulative_raw += weight_per_batch
        running_physical_total += weight_per_batch

        # Gram Stripping Logic
        safe_raw = round(cumulative_raw, 7)
        kilos_fixed = math.floor(round(safe_raw * 100, 1)) / 100.0
        gram_remainder = round((safe_raw - kilos_fixed) * 1000, 4)

        if 0.000001 < gram_remainder <= 30.0:
            d_large, d_small = kilos_fixed, gram_remainder
        else:
            d_large, d_small = cumulative_raw, 0.0

        # Insert final row
        insert_production_row(target_table, material_code, d_large, d_small, weight_total_full)


# --- HELPERS ---

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