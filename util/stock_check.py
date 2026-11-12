from collections import defaultdict

from PyQt6.QtWidgets import QMessageBox

# Set to True once the stock database is ready.
# While False, validation always passes and deduction does nothing.
STOCK_DB_READY = False


def _norm(name):
    return str(name).strip().upper()


# ==========================================
# 1. READ THE TABLE (first column + last column)
# ==========================================
def get_table_materials(table):
    """Returns {MATERIAL_NAME: total_weight} from any materials_table.
    Uses column 0 (name) and the LAST column (total weight).
    Blank/separator rows are skipped; duplicate names are summed."""
    last_col = table.columnCount() - 1
    totals = defaultdict(float)

    for row in range(table.rowCount()):
        name_item = table.item(row, 0)
        weight_item = table.item(row, last_col)

        name = _norm(name_item.text()) if name_item else ""
        if not name:
            continue

        try:
            text = weight_item.text().replace(",", "").strip() if weight_item else ""
            weight = float(text) if text else 0.0
        except ValueError:
            weight = 0.0

        totals[name] += weight

    return dict(totals)


# ==========================================
# 2. DATABASE STUBS (replace when DB is ready)
# ==========================================
def fetch_stock_on_hand(material_names):
    """Should return {MATERIAL_NAME: total_stock_on_hand} for the given names.
    Materials that don't exist in the stock table must simply be left out.

    TODO: move to db/read.py and query something like:
        SELECT material_name, total_stock_on_hand
        FROM <stock_table>
        WHERE material_name IN (...)
    """
    return {}


def apply_stock_deduction(deductions):
    """deductions = {MATERIAL_NAME: weight_to_deduct}.
    Should subtract each weight from that material's stock on hand.
    Return (success: bool, message: str).

    TODO: move to db/write.py and run as one transaction:
        UPDATE <stock_table>
        SET total_stock_on_hand = total_stock_on_hand - %s
        WHERE material_name = %s
    """
    return True, ""


# ==========================================
# 3. VALIDATION (before saving)
# ==========================================
def validate_stock(table, ignore_unlisted=False):
    """Returns (ok, issues).
    ignore_unlisted=True  -> materials not in the stock list are skipped silently (manual entry)
    ignore_unlisted=False -> materials not in the stock list are reported (auto entries)
    """
    if not STOCK_DB_READY:
        return True, []

    required = get_table_materials(table)
    if not required:
        return True, []

    stock = fetch_stock_on_hand(list(required.keys()))
    issues = []

    for name, needed in required.items():
        if name not in stock:
            if not ignore_unlisted:
                issues.append(f"{name}: not found in stock list")
            continue

        available = float(stock[name])
        if needed - available > 1e-9:
            issues.append(f"{name}: needs {needed:.6f}, only {available:.6f} on hand")

    return len(issues) == 0, issues


def check_stock_before_save(parent, table, ignore_unlisted=False):
    """Runs validate_stock and shows a popup. Returns True if saving may continue."""
    ok, issues = validate_stock(table, ignore_unlisted)
    if not ok:
        QMessageBox.warning(parent, "Insufficient Stock",
                            "Cannot save. Please check the following materials:\n\n" + "\n".join(issues))
    return ok


# ==========================================
# 4. DEDUCTION (after a successful save)
# ==========================================
def deduct_stock_on_save(table, ignore_unlisted=False):
    """Deducts the table's materials from stock. Returns (success, message)."""
    if not STOCK_DB_READY:
        return True, ""

    required = get_table_materials(table)
    if not required:
        return True, ""

    stock = fetch_stock_on_hand(list(required.keys()))

    deductions = {}
    for name, weight in required.items():
        if name in stock:
            deductions[name] = weight
        elif not ignore_unlisted:
            return False, f"{name} not found in stock list."

    if not deductions:
        return True, ""

    return apply_stock_deduction(deductions)