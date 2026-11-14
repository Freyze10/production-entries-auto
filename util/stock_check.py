"""
stock_check.py  (READ-ONLY stock validation, nothing is ever written to stock)

Rule set
--------
available = view A stock - reserved

reserved  = SUM(tbl_production02.total_weight) per material, only for rows where
            - prod_id is NOT in the "excluded" list (view B)
            - prod_id >= the lowest prod_id in view B (older records are never computed)
            - tbl_production01.is_deleted = FALSE
            - tbl_production02.is_deleted = FALSE
            - prod_id is not the record currently being saved (its old rows are ignored)

Update rules (checked fresh from the database on every save)
            1. confirmation_encoded_on has a value -> blocked (already confirmed)
            2. prod_id is in view B                -> blocked (already prepared)
            3. otherwise                           -> allowed, validated like a new record

View B
            - If it has a prod_id column, that is used directly.
            - If not, prep_id is read from it and resolved to prod_id(s) through the old
              .dbf database (one prep_id can map to several prod_ids).
"""
import logging
import os
import threading
import time
from collections import defaultdict

from PyQt6.QtWidgets import QMessageBox

from db.connection import get_connection

try:
    from dbfread import DBF, DBFNotFound
except ImportError:  # keeps the module importable if dbfread is missing
    DBF = None
    DBFNotFound = FileNotFoundError

log = logging.getLogger(__name__)

# ==========================================
# SETTINGS (change these, the logic stays the same)
# ==========================================
# While False, validation always passes.
STOCK_DB_READY = True

# --- PostgreSQL objects (schemas come from .env) ---
PRODUCTION_SCHEMA = os.environ.get('PRODUCTION_SCHEMA')   # tbl_production01 / tbl_production02
VIEW_SCHEMA = os.environ.get('VIEW_SCHEMA')               # view_adjusted_ending_overall / view_encoded_prep (set this in .env)
STOCK_VIEW = "view_adjusted_ending_overall"        # view A
STOCK_CODE_COL = "rmcode"
STOCK_QTY_COL = "overall_qty"
EXCLUDE_VIEW = "view_encoded_prep"           # view B
EXCLUDE_PREP_COL = "prep_form_no"
EXCLUDE_PROD_COL = "prod_id"             # may not exist yet, detected automatically

# --- Old .dbf database (placeholders, used only while view B has no prod_id column) ---
DBF_BASE_PATH = r'\\system-server\SYSTEM-NEW-OLD'
PREPERATION_DBF = os.path.join(DBF_BASE_PATH, 'tbl_wh3.dbf')
DBF_PREP_FIELD = 'T_PID'
DBF_PROD_FIELD = 'T_PRODID'
DBF_CACHE_SECONDS = 300                  # how long a scanned prep_id -> prod_id map is reused

SERVER_UNREACHABLE_MSG = "System server is unreachable. Please try again later."


class StockCheckError(Exception):
    """A blocking problem that is not a simple 'insufficient stock' list."""

    def __init__(self, message, title="Stock Check"):
        super().__init__(message)
        self.message = message
        self.title = title


def _norm(name):
    return str(name).strip().upper()


def _key(value):
    """Normalizes ids coming from the view or the DBF so they can be compared."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value).strip()


def _to_int(value):
    try:
        if value is None or str(value).strip() == "":
            return None
        return int(float(str(value).strip()))
    except (ValueError, TypeError):
        return None


# ==========================================
# 1. READ THE TABLE (material name + total weight)
# ==========================================
def get_table_materials(table, weight_col=3):
    """Returns {MATERIAL_NAME: total_weight}. Column 0 = name, weight_col = total weight
    (3 in all three save screens). Blank/separator rows are skipped; duplicates are summed."""
    totals = defaultdict(float)

    for row in range(table.rowCount()):
        name_item = table.item(row, 0)
        weight_item = table.item(row, weight_col)

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
# 2. DBF LOOKUP (prep_id -> prod_id), only used while view B has no prod_id column
# ==========================================
_dbf_lock = threading.Lock()
_dbf_cache = {"map": {}, "loaded_at": 0.0}


def _scan_dbf(wanted):
    """One forward pass over the DBF. Keeps only the prep_ids we asked for.
    dbfread skips records flagged as deleted by default."""
    if DBF is None:
        raise StockCheckError("The 'dbfread' package is not installed.", "Stock Check")

    found = defaultdict(set)
    try:
        table = DBF(
            PREPERATION_DBF,
            lowernames=True,
            load=False,
            ignore_missing_memofile=True,
            char_decode_errors="ignore",
        )
        prep_field = DBF_PREP_FIELD.lower()
        prod_field = DBF_PROD_FIELD.lower()

        for rec in table:
            prep = _key(rec.get(prep_field))
            if prep in wanted:
                pid = _to_int(rec.get(prod_field))
                if pid is not None:
                    found[prep].add(pid)
    except (OSError, DBFNotFound):
        raise StockCheckError(SERVER_UNREACHABLE_MSG, "Server Unreachable")

    return found


def resolve_prep_to_prod(prep_ids):
    """Returns the set of prod_ids that belong to the given prep_ids (via the DBF, cached)."""
    wanted = {_key(p) for p in prep_ids if _key(p)}
    if not wanted:
        return set()

    with _dbf_lock:
        age = time.time() - _dbf_cache["loaded_at"]
        cached = _dbf_cache["map"]

        if age >= DBF_CACHE_SECONDS or not wanted.issubset(cached.keys()):
            found = _scan_dbf(wanted)
            # prep_ids not found stay in the map (empty) so we don't rescan on every save
            new_map = {w: set(found.get(w, set())) for w in wanted}
            _dbf_cache["map"] = new_map
            _dbf_cache["loaded_at"] = time.time()
            cached = new_map

            for w in wanted:
                if not cached[w]:
                    log.warning("prep_id %s was not found in the DBF; its materials count as reserved.", w)

        result = set()
        for w in wanted:
            result |= cached.get(w, set())
        return result


# ==========================================
# 3. DATABASE READS (all read-only)
# ==========================================
def _view_has_column(cur, view, column):
    cur.execute(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s AND column_name = %s
        LIMIT 1
        """,
        (VIEW_SCHEMA, view, column),
    )
    return cur.fetchone() is not None


def get_excluded_prod_ids(cur):
    """Set of prod_ids that are excluded from the reserved computation (view B)."""
    view = f'{VIEW_SCHEMA}."{EXCLUDE_VIEW}"'

    if _view_has_column(cur, EXCLUDE_VIEW, EXCLUDE_PROD_COL):
        cur.execute(f'SELECT DISTINCT "{EXCLUDE_PROD_COL}" FROM {view} WHERE "{EXCLUDE_PROD_COL}" IS NOT NULL')
        ids = {_to_int(r[0]) for r in cur.fetchall()}
        ids.discard(None)
    else:
        cur.execute(f'SELECT DISTINCT "{EXCLUDE_PREP_COL}" FROM {view} WHERE "{EXCLUDE_PREP_COL}" IS NOT NULL')
        preps = [r[0] for r in cur.fetchall()]
        ids = resolve_prep_to_prod(preps)

    if not ids:
        raise StockCheckError(
            "The list of prepared productions is empty or could not be matched, "
            "so stock cannot be verified. Please contact the administrator.",
            "Stock Check",
        )
    return ids


def fetch_stock_on_hand(cur, material_names):
    """{MATERIAL_NAME: stock} from view A. Materials not in the view are left out."""
    if not material_names:
        return {}

    cur.execute(
        f"""
        SELECT UPPER(TRIM("{STOCK_CODE_COL}")) AS code, "{STOCK_QTY_COL}"
        FROM {VIEW_SCHEMA}."{STOCK_VIEW}"
        WHERE UPPER(TRIM("{STOCK_CODE_COL}")) = ANY(%s)
        """,
        (list(material_names),),
    )
    stock = defaultdict(float)
    for code, qty in cur.fetchall():
        stock[code] += float(qty or 0)
    return dict(stock)


def fetch_reserved(cur, material_names, excluded_ids, current_prod_id):
    """{MATERIAL_NAME: (reserved_total, [prod_ids holding it])} for unprepared records."""
    if not material_names:
        return {}

    cutoff = min(excluded_ids)

    cur.execute(
        f"""
        SELECT UPPER(TRIM(p2.material_code)) AS code,
               SUM(p2.total_weight)          AS reserved,
               ARRAY_AGG(DISTINCT p2.prod_id ORDER BY p2.prod_id) AS holders
        FROM {PRODUCTION_SCHEMA}.tbl_production02 p2
        JOIN {PRODUCTION_SCHEMA}.tbl_production01 p1 ON p1.prod_id = p2.prod_id
        WHERE COALESCE(p1.is_deleted, FALSE) = FALSE
          AND COALESCE(p2.is_deleted, FALSE) = FALSE
          AND p2.prod_id >= %s
          AND NOT (p2.prod_id = ANY(%s))
          AND p2.prod_id <> %s
          AND TRIM(COALESCE(p2.material_code, '')) <> ''
          AND UPPER(TRIM(p2.material_code)) = ANY(%s)
        GROUP BY 1
        """,
        (cutoff, list(excluded_ids), current_prod_id, list(material_names)),
    )
    return {code: (float(total or 0), list(holders or [])) for code, total, holders in cur.fetchall()}


def fetch_record_status(cur, prod_id):
    """Returns {'confirmed': bool, 'deleted': bool} or None if the prod_id doesn't exist.
    Confirmed = tbl_production_encode.confirmation_encoded_on has a value."""
    cur.execute(
        f"""
        SELECT e.confirmation_encoded_on, COALESCE(p1.is_deleted, FALSE)
        FROM {PRODUCTION_SCHEMA}.tbl_production01 p1
        LEFT JOIN {PRODUCTION_SCHEMA}.tbl_production_encode e ON e.prod_id = p1.prod_id
        WHERE p1.prod_id = %s
        """,
        (prod_id,),
    )
    row = cur.fetchone()
    if row is None:
        return None
    return {"confirmed": row[0] is not None, "deleted": bool(row[1])}

def print_all_available_stocks():
    """Console only. Prints the remaining stock of every raw material in view A:
    available = stock - reserved by unprepared productions (same rules as validate_stock).
    Never raises, so it can't break the screen."""
    try:
        if not STOCK_DB_READY or not PRODUCTION_SCHEMA or not VIEW_SCHEMA:
            print("[stock overview] skipped: STOCK_DB_READY is False or schemas not set in .env", flush=True)
            return

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                excluded = get_excluded_prod_ids(cur)
                cutoff = min(excluded)

                cur.execute(
                    f"""
                    SELECT UPPER(TRIM("{STOCK_CODE_COL}")) AS code, SUM("{STOCK_QTY_COL}")
                    FROM {VIEW_SCHEMA}."{STOCK_VIEW}"
                    GROUP BY 1
                    """
                )
                stock = {code: float(qty or 0) for code, qty in cur.fetchall() if code}

                cur.execute(
                    f"""
                                    SELECT UPPER(TRIM(p2.material_code)) AS code,
                                           SUM(p2.total_weight) AS reserved,
                                           ARRAY_AGG(DISTINCT p2.prod_id ORDER BY p2.prod_id) AS holders
                                    FROM {PRODUCTION_SCHEMA}.tbl_production02 p2
                                    JOIN {PRODUCTION_SCHEMA}.tbl_production01 p1 ON p1.prod_id = p2.prod_id
                                    WHERE COALESCE(p1.is_deleted, FALSE) = FALSE
                                      AND COALESCE(p2.is_deleted, FALSE) = FALSE
                                      AND p2.prod_id >= %s
                                      AND NOT (p2.prod_id = ANY(%s))
                                      AND TRIM(COALESCE(p2.material_code, '')) <> ''
                                    GROUP BY 1
                                    """,
                    (cutoff, list(excluded)),
                )
                reserved_rows = cur.fetchall()
                reserved = {code: float(total or 0) for code, total, _ in reserved_rows}
                holders = {code: list(h or []) for code, _, h in reserved_rows}
        finally:
            try:
                conn.rollback()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass

        rows = []
        for code, on_hand in stock.items():
            res = reserved.get(code, 0.0)
            rows.append((code, on_hand, res, on_hand - res))
        rows.sort(key=lambda r: r[3])  # lowest available first; use r[0] to sort A-Z instead

        low = sum(1 for r in rows if r[3] <= 0)
        print(f"\n===== AVAILABLE RAW MATERIAL STOCKS ({len(rows)} materials, {low} at or below zero) =====")
        print(f"Cutoff prod_id (lowest in view B): {cutoff} | view B has {len(excluded)} prod_ids "
              f"(lowest 5: {sorted(excluded)[:5]})")
        print(f"{'MATERIAL':<26}{'STOCK':>16}{'RESERVED':>16}{'AVAILABLE':>16}  STATUS / HOLDERS")
        for code, on_hand, res, avail in rows:
            status = "OUT / NEGATIVE" if avail < 0 else ("ZERO" if avail == 0 else "")
            if avail < 0:
                h = holders.get(code, [])
                status += f"  prod IDs: {', '.join(map(str, h[:15]))}{' ...' if len(h) > 15 else ''}"
            print(f"{code[:25]:<26}{on_hand:>16.6f}{res:>16.6f}{avail:>16.6f}  {status}")
        print("=" * 100, flush=True)
    except Exception as e:
        import traceback
        print(f"[stock overview skipped] {e}")
        traceback.print_exc()

# ==========================================
# 4. VALIDATION (before saving)
# ==========================================

def validate_stock(table, prod_id_raw, is_update, ignore_unlisted=False):
    """Returns (ok, issues). Raises StockCheckError for blocking problems
    (update not allowed, server unreachable, ...).
    ignore_unlisted=True  -> materials not in view A are skipped silently (manual entry)
    ignore_unlisted=False -> materials not in view A are reported (auto entries)
    """
    if not STOCK_DB_READY:
        return True, []

    if not PRODUCTION_SCHEMA or not VIEW_SCHEMA:
        raise StockCheckError("PRODUCTION_SCHEMA or VIEW_SCHEMA is not set in the .env file.", "Configuration Error")

    prod_id = _to_int(prod_id_raw)
    if prod_id is None:
        raise StockCheckError("Production ID must be a number.", "Validation Error")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            excluded = get_excluded_prod_ids(cur)

            # ---- update rules (fresh from the database every save) ----
            if is_update:
                status = fetch_record_status(cur, prod_id)
                if status is None:
                    raise StockCheckError(f"Production {prod_id} does not exist, so it cannot be updated.",
                                          "Cannot Update")
                if status["confirmed"]:
                    raise StockCheckError("This production record is already confirmed and can no longer be edited.",
                                          "Cannot Update")
                if prod_id in excluded:
                    raise StockCheckError("This prod id is already prepared, please confirm this production form.",
                                          "Cannot Update")

            # ---- stock check ----
            required = {n: w for n, w in get_table_materials(table).items() if w > 0}
            if not required:
                return True, []

            names = list(required.keys())
            stock = fetch_stock_on_hand(cur, names)
            reserved = fetch_reserved(cur, names, excluded, prod_id)
    finally:
        try:
            conn.rollback()  # nothing was written; just release the transaction
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

    issues = []
    for name, needed in required.items():
        if name not in stock:
            if not ignore_unlisted:
                issues.append(f"{name}: not found in stock list")
            continue

        on_hand = stock[name]
        res_total, holders = reserved.get(name, (0.0, []))
        available = on_hand - res_total

        if needed - available > 1e-9:
            msg = (f"{name}: needs {needed:.6f}, only {max(available, 0.0):.6f} available "
                   f"(stock {on_hand:.6f}, reserved {res_total:.6f}")
            if holders:
                shown = ", ".join(str(h) for h in holders[:10])
                if len(holders) > 10:
                    shown += ", ..."
                msg += f" by prod ID {shown}"
            issues.append(msg + ")")

    return len(issues) == 0, issues


def check_stock_before_save(parent, table, prod_id_raw, is_update, ignore_unlisted=False):
    """Runs validate_stock and shows a popup. Returns True if saving may continue."""
    try:
        ok, issues = validate_stock(table, prod_id_raw, is_update, ignore_unlisted)
    except StockCheckError as e:
        QMessageBox.warning(parent, e.title, e.message)
        return False
    except Exception as e:  # DB error etc.: block, because the check could not be trusted
        log.exception("Stock check failed")
        QMessageBox.critical(parent, "Stock Check Failed", f"Unable to verify stock. Saving was stopped.\n\n{e}")
        return False

    if not ok:
        QMessageBox.warning(parent, "Insufficient Stock",
                            "Cannot save. Please check the following materials:\n\n" + "\n".join(issues))
    return ok