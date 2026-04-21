import math
from PyQt6.QtWidgets import QTableWidgetItem
from util.field_format import NumericTableWidgetItem
from util.format_rm_note import get_bag_limit


def compute_generate(source_table, target_table, total_weight, batch_divisor, base_divisor=100.0):
    """
    Generate Function with Priority Splitting and Dynamic Bag Limits:
    - First and Last rows are NEVER split, even if they exceed the limit.
    - Other rows are sliced into bag-limit-sized pieces.
    """
    target_table.setRowCount(0)
    cumulative_raw = 0.0
    running_physical_total = 0.0
    total_rows = source_table.rowCount()

    # --- INITIALIZE LIMIT ---
    if total_rows > 0:
        first_mat = source_table.item(0, 0).text().strip()
        current_limit = get_bag_limit(first_mat)
    else:
        current_limit = 25.0

    factor = total_weight / base_divisor

    for row in range(total_rows):
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
            insert_production_row(target_table, material_code, 0.0, weight_per_batch * 1000, weight_total_full)
            continue

        # --- CASE 2: BIG MATERIAL SPLITTING ---
        # Logic: Split if over limit, UNLESS it is the first row or the last row
        is_first_row = (row == 0)
        is_last_row = (row == total_rows - 1)

        if weight_per_batch > current_limit and not is_first_row and not is_last_row:
            # If we were already accumulating, add separator
            if running_physical_total > 0:
                insert_separator(target_table)
                current_limit = get_bag_limit(material_code)
                running_physical_total = 0.0
                cumulative_raw = 0.0

            remaining_item_weight = weight_per_batch

            while remaining_item_weight > current_limit:
                slice_total = (current_limit / weight_per_batch) * weight_total_full
                insert_production_row(target_table, material_code, current_limit, 0.0, slice_total)
                insert_separator(target_table)

                current_limit = get_bag_limit(material_code)
                remaining_item_weight -= current_limit
                running_physical_total = 0.0
                cumulative_raw = 0.0

            weight_total_full = (remaining_item_weight / weight_per_batch) * weight_total_full
            weight_per_batch = remaining_item_weight

        # --- CASE 3: NORMAL MATERIAL ACCUMULATION ---
        # This will still trigger for the first/last row if they are heavy,
        # which is good (it puts them in their own bag/section).
        if (running_physical_total + weight_per_batch) > current_limit:
            if target_table.rowCount() > 0:
                insert_separator(target_table)

            current_limit = get_bag_limit(material_code)
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

        cumulative_raw = d_large

        # Insert final row (or the full row if it was first/last)
        insert_production_row(target_table, material_code, d_large, d_small, weight_total_full)


# --- HELPERS (Keep these the same) ---

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