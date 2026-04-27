import collections
import os
import traceback
import datetime

import dbfread
from PyQt6.QtCore import pyqtSignal, QObject
from sqlalchemy import text, create_engine

from db.connection import get_connection

# --- Database Connection Config ---
temp_conn = get_connection()
DB_CONFIG = {
    "host": temp_conn.info.host,
    "port": temp_conn.info.port,
    "dbname": temp_conn.info.dbname,
    "user": temp_conn.info.user,
    "password": temp_conn.info.password
}
temp_conn.close()

DBF_BASE_PATH = r'\\system-server\SYSTEM-NEW-OLD'
FORMULA_PRIMARY_DBF_PATH = os.path.join(DBF_BASE_PATH, 'tbl_formula01.dbf')
FORMULA_ITEMS_DBF_PATH = os.path.join(DBF_BASE_PATH, 'tbl_formula02.dbf')
PRODUCTION_PRIMARY_DBF_PATH = os.path.join(DBF_BASE_PATH, 'tbl_prod01.dbf')
PRODUCTION_ITEMS_DBF_PATH = os.path.join(DBF_BASE_PATH, 'tbl_prod02.dbf')
RM_WH = os.path.join(DBF_BASE_PATH, 'tbl_rm_wh.dbf')
RM_INCOMING = os.path.join(DBF_BASE_PATH, 'tbl_incoming.dbf')

try:
    db_url = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=3600)
except Exception as e:
    print(f"CRITICAL: Could not create database engine. Error: {e}")


# --- Data Conversion Helpers ---

def _to_bool(value):
    """Converts DBF logical (True/False) or strings ('T'/'F') to Python boolean."""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    v_str = str(value).strip().upper()
    # Handle standard VFP/DBF logical markers
    if v_str in ('T', '.T.', 'Y', '1', 'TRUE', 'YES'):
        return True
    return False


def _to_float(value, default=0.0):
    if value is None: return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _to_int(value, default=None):
    if value is None: return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def _to_str(value, default=''):
    if value is None: return default
    if isinstance(value, bytes):
        try:
            return value.decode('latin1').replace('\x00', '').strip() or default
        except:
            return default
    return str(value).replace('\x00', '').strip() or default


def _is_valid_date(d):
    """Checks if date is valid and not the VFP 'zero' date (1899)."""
    if d is None: return False
    try:
        if isinstance(d, (datetime.date, datetime.datetime)):
            return d.year >= 1900
        s = str(d).strip()
        return bool(s) and not s.startswith('1899')
    except:
        return False


class Sync(QObject):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)

    def run(self):
        try:
            # Get Current Max IDs to avoid duplicate processing
            with engine.connect() as conn:
                max_form_id = conn.execute(text("SELECT COALESCE(MAX(form_id), 0) FROM tbl_formula01")).scalar() or 0
                max_prod_id = conn.execute(text("SELECT COALESCE(MAX(prod_id), 0) FROM tbl_production01")).scalar() or 0

            self.progress.emit(f"Phase 1/3: Reading legacy items...")

            items_by_uid = collections.defaultdict(list)
            items_by_prod_id = collections.defaultdict(list)

            # 1. READ SUB-ITEMS (FORMULA 02)
            dbf_f_items = dbfread.DBF(FORMULA_ITEMS_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for item in dbf_f_items:
                uid = _to_int(item.get('T_UID'))
                if uid is None or uid <= max_form_id: continue
                items_by_uid[uid].append({
                    "uid": uid,
                    "seq": _to_int(item.get('T_SEQ')),
                    "material_code": _to_str(item.get('T_MATCODE')),
                    "concentration": _to_float(item.get('T_CON')),
                    "is_deleted": _to_bool(item.get('T_DELETED'))  # BOOLEAN
                })

            # 2. READ SUB-ITEMS (PROD 02)
            dbf_p_items = dbfread.DBF(PRODUCTION_ITEMS_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for item in dbf_p_items:
                pid = _to_int(item.get('T_PRODID'))
                if pid is None or pid <= max_prod_id: continue
                items_by_prod_id[pid].append({
                    "prod_id": pid, "seq": _to_int(item.get('T_SEQ')),
                    "material_code": _to_str(item.get('T_MATCODE')),
                    "large_scale": _to_float(item.get('T_PRODA')),
                    "small_scale": _to_float(item.get('T_LABA')),
                    "total_weight": _to_float(item.get('T_WT')),
                    "total_loss": _to_float(item.get('T_LOSS')),
                    "total_consumption": _to_float(item.get('T_CONS')),
                    "is_deleted": _to_bool(item.get('T_DELETED'))  # BOOLEAN
                })

            self.progress.emit("Phase 2/3: Reading primary records...")

            # 3. READ FORMULA PRIMARY
            primary_recs = []
            dbf_primary = dbfread.DBF(FORMULA_PRIMARY_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for r in dbf_primary:
                uid = _to_int(r.get('T_UID'))
                if uid is None or uid <= max_form_id: continue
                primary_recs.append({
                    "uid": uid, "index_no": _to_str(r.get('T_INDEX')),
                    "date": r.get('T_DATE'), "customer": _to_str(r.get('T_CUSTOMER')),
                    "prod_code": _to_str(r.get('T_PRODCODE')), "prod_color": _to_str(r.get('T_PRODCOLO')),
                    "dosage": _to_float(r.get('T_DOSAGE')), "ld": _to_float(r.get('T_LD')),
                    "total_concentration": _to_float(r.get('T_TOTALCON')), "mix_time": _to_str(r.get('T_MIX')),
                    "resin": _to_str(r.get('T_RESIN')), "application": _to_str(r.get('T_APP')),
                    "cm_num": _to_str(r.get('T_CMNUM')),
                    "cm_date": r.get('T_CMDATE') if _is_valid_date(r.get('T_CMDATE')) else None,
                    "notes": _to_str(r.get('T_REM')), "date_time": _to_str(r.get('T_UDATE')),
                    "is_deleted": _to_bool(r.get('T_DELETED')),  # BOOLEAN
                    "is_used": _to_bool(r.get('T_USED')),  # BOOLEAN
                    # Extra metadata for tbl_formula_encode
                    "matched_by": _to_str(r.get('T_MATCHBY')), "encoded_by": _to_str(r.get('T_ENCODEB')),
                    "updated_by": _to_str(r.get('T_UPDATEBY'))
                })

            # 4. READ PRODUCTION PRIMARY
            prod_recs = []
            dbf_prod = dbfread.DBF(PRODUCTION_PRIMARY_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for r in dbf_prod:
                pid = _to_int(r.get('T_PRODID'))
                if pid is None or pid <= max_prod_id: continue

                # Logic for note and printed status
                rem = _to_str(r.get('T_REMARKS'))
                note_raw = _to_str(r.get('T_NOTE'))
                note = f"{note_raw}\n{rem}".strip() if rem else note_raw
                is_printed = (_to_str(r.get('T_JDONE')).upper() == "PRINTED")

                prod_recs.append({
                    "prod_id": pid, "prod_date": r.get('T_PRODDATE'),
                    "customer": _to_str(r.get('T_CUSTOMER')), "form_id": _to_int(r.get('T_FID')),
                    "index_no": _to_str(r.get('T_INDEX')), "prod_code": _to_str(r.get('T_PRODCODE')),
                    "prod_color": _to_str(r.get('T_PRODCOLO')), "dosage": _to_float(r.get('T_DOSAGE')),
                    "ld": _to_float(r.get('T_LD')), "lot_no": _to_str(r.get('T_LOTNUM')),
                    "order_no": _to_str(r.get('T_ORDERNUM')), "colormatch_no": _to_str(r.get('T_CMNUM')),
                    "colormatch_date": r.get('T_CMDATE'), "mix_time": _to_str(r.get('T_MIXTIME')),
                    "machine_no": _to_str(r.get('T_MACHINE')), "note": note,
                    "user_id": _to_str(r.get('T_USERID')), "form_type": _to_str(r.get('T_FTYPE')),
                    "inventory_c_date": r.get('T_CDATE'),
                    "is_deleted": _to_bool(r.get('T_DELETED')),  # BOOLEAN
                    "is_printed": is_printed,  # BOOLEAN
                    # Extra metadata for tbl_production_encode and quantity
                    "prepared_by": _to_str(r.get('T_PREPARED')), "encoded_by": _to_str(r.get('T_ENCODEDB')),
                    "encoded_on": r.get('T_ENCODEDO'), "conf_encoded_on": r.get('T_SDATE'),
                    "qty_req": _to_float(r.get('T_QTYREQ')), "qty_batch": _to_float(r.get('T_QTYBATCH')),
                    "qty_prod": _to_float(r.get('T_QTYPROD'))
                })

            if not primary_recs and not prod_recs:
                self.finished.emit(True, "Sync Info: No new records found.")
                return

            # Phase 3: Writing to PostgreSQL
            self.progress.emit("Phase 3/3: Committing to PostgreSQL...")
            with engine.connect() as conn:
                with conn.begin():
                    # --- Commit Formula ---
                    if primary_recs:
                        conn.execute(text("""
                            INSERT INTO tbl_formula01 (form_id, index_no, date, customer, prod_code, prod_color, dosage, total_concentration, ld, mix_time, resin, application, colormatch_no, colormatch_date, notes, date_time, is_deleted, is_used)
                            VALUES (:uid, :index_no, :date, :customer, :prod_code, :prod_color, :dosage, :total_concentration, :ld, :mix_time, :resin, :application, :cm_num, :cm_date, :notes, :date_time, :is_deleted, :is_used)
                            ON CONFLICT (form_id) DO UPDATE SET is_deleted = EXCLUDED.is_deleted, is_used = EXCLUDED.is_used
                        """), primary_recs)

                        conn.execute(text("""
                            INSERT INTO tbl_formula_encode (form_id, match_by, encoded_by, updated_by)
                            VALUES (:uid, :matched_by, :encoded_by, :updated_by) ON CONFLICT DO NOTHING
                        """), primary_recs)

                        all_f_items = [i for r in primary_recs for i in items_by_uid.get(r['uid'], [])]
                        if all_f_items:
                            conn.execute(text(
                                "INSERT INTO tbl_formula02 (form_id, sequence_no, material_code, concentration, is_deleted) VALUES (:uid, :seq, :material_code, :concentration, :is_deleted)"),
                                         all_f_items)

                    # --- Commit Production ---
                    if prod_recs:
                        conn.execute(text("""
                            INSERT INTO tbl_production01 (prod_id, prod_date, customer, form_id, index_no, prod_code, prod_color, dosage, ld, lot_no, order_no, colormatch_no, colormatch_date, mix_time, machine_no, note, user_id, is_deleted, is_printed, inventory_c_date, form_type)
                            VALUES (:prod_id, :prod_date, :customer, :form_id, :index_no, :prod_code, :prod_color, :dosage, :ld, :lot_no, :order_no, :colormatch_no, :colormatch_date, :mix_time, :machine_no, :note, :user_id, :is_deleted, :is_printed, :inventory_c_date, :form_type)
                            ON CONFLICT (prod_id) DO UPDATE SET is_deleted = EXCLUDED.is_deleted, is_printed = EXCLUDED.is_printed
                        """), prod_recs)

                        conn.execute(text("""
                            INSERT INTO tbl_production_encode (prod_id, prepared_by, encoded_by, encoded_on, confirmation_encoded_on)
                            VALUES (:prod_id, :prepared_by, :encoded_by, :encoded_on, :conf_encoded_on) ON CONFLICT DO NOTHING
                        """), prod_recs)

                        conn.execute(text("""
                            INSERT INTO tbl_production_quantity (prod_id, quantity_req, quantity_batch, quantity_prod)
                            VALUES (:prod_id, :qty_req, :qty_batch, :qty_prod) ON CONFLICT DO NOTHING
                        """), prod_recs)

                        all_p_items = [i for r in prod_recs for i in items_by_prod_id.get(r['prod_id'], [])]
                        if all_p_items:
                            conn.execute(text("""
                                INSERT INTO tbl_production02 (prod_id, sequence_no, material_code, large_scale, small_scale, total_weight, is_deleted, total_loss, total_consumption)
                                VALUES (:prod_id, :seq, :material_code, :large_scale, :small_scale, :total_weight, :is_deleted, :total_loss, :total_consumption)
                                ON CONFLICT DO NOTHING
                            """), all_p_items)

            # 5. SYNC RM INCOMING (Call logic from helper)
            self.progress.emit("Finalizing: Syncing RM Incoming...")
            perform_rm_incoming_sync_logic(engine)

            self.finished.emit(True, "Legacy sync successful.")

        except Exception as e:
            traceback.print_exc()
            self.finished.emit(False, f"Critical Sync Error: {e}")


class SyncRM(QObject):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)

    def run(self):
        """Syncs the warehouse Raw Material list."""
        try:
            self.progress.emit("Reading Warehouse DBF...")
            unique_rm_codes = set()
            dbf = dbfread.DBF(RM_WH, encoding='latin1', char_decode_errors='ignore')
            for r in dbf:
                code = _to_str(r.get('T_MATCODE'))
                # Use _to_bool for deleted check
                if _to_bool(r.get('T_DELETED')) or not code: continue
                unique_rm_codes.add(code)

            data = [{"rm_code": code} for code in unique_rm_codes]
            with engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("TRUNCATE TABLE tbl_raw_material_list RESTART IDENTITY CASCADE"))
                    conn.execute(text("INSERT INTO tbl_raw_material_list (rm_code) VALUES (:rm_code)"), data)
            self.finished.emit(True, "Raw Material list updated.")
        except Exception as e:
            self.finished.emit(False, str(e))


def perform_rm_incoming_sync_logic(engine, progress_callback=None):
    """Core logic to sync incoming warehouse materials."""
    dbf = dbfread.DBF(RM_INCOMING, encoding='latin1', char_decode_errors='ignore')
    latest_by_code = {}

    for r in dbf:
        if _to_bool(r.get('T_DELETED')): continue
        mat_code = _to_str(r.get('T_MATCODE'))
        if not mat_code: continue

        raw_date = r.get('T_DATE')
        is_valid = _is_valid_date(raw_date)

        # Keep only the newest record per material code
        if mat_code not in latest_by_code or (
                is_valid and (not latest_by_code[mat_code]['date'] or raw_date > latest_by_code[mat_code]['date'])):
            latest_by_code[mat_code] = {
                "material_code": mat_code,
                "note": _to_str(r.get('T_NOTE')),
                "date": raw_date if is_valid else None
            }

    if not latest_by_code: return 0

    data = list(latest_by_code.values())
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text("""
                INSERT INTO tbl_rm_incoming (date, material_code, note)
                VALUES (:date, :material_code, :note)
                ON CONFLICT (material_code) DO UPDATE SET note = EXCLUDED.note, date = EXCLUDED.date
            """), data)
    return len(data)