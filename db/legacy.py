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
    if value is None: return False
    if isinstance(value, bool): return value
    v_str = str(value).strip().upper()
    if v_str in ('T', '.T.', 'Y', '1', 'TRUE', 'YES'): return True
    return False


def _to_float(value, default=0.0):
    if value is None: return default
    try:
        return float(value)
    except:
        return default


def _to_int(value, default=None):
    if value is None: return default
    try:
        return int(float(value))
    except:
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
    if d is None: return False
    try:
        if isinstance(d, (datetime.date, datetime.datetime)): return d.year >= 1900
        s = str(d).strip()
        return bool(s) and not s.startswith('1899')
    except:
        return False


class Sync(QObject):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)

    def run(self):
        try:
            # 1. Get current state from PostgreSQL
            with engine.connect() as conn:
                max_form_id = conn.execute(text("SELECT COALESCE(MAX(form_id), 0) FROM tbl_formula01")).scalar() or 0
                max_prod_id = conn.execute(text("SELECT COALESCE(MAX(prod_id), 0) FROM tbl_production01")).scalar() or 0

                # Fetch mapping of existing production IDs and their printed status
                # result looks like: {1001: True, 1002: False...}
                pg_status_map = {row[0]: row[1] for row in
                                 conn.execute(text("SELECT prod_id, is_printed FROM tbl_production01")).fetchall()}

            self.progress.emit("Phase 1/3: Scanning legacy for new or changed records...")

            target_prod_ids = set()
            target_form_uids = set()

            # --- IDENTIFY WHICH PRODUCTION RECORDS NEED SYNCING ---
            dbf_prod_scan = dbfread.DBF(PRODUCTION_PRIMARY_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for r in dbf_prod_scan:
                pid = _to_int(r.get('T_PRODID'))
                if pid is None: continue

                # Logic: Is it new OR has the Printed status changed?
                legacy_is_printed = (_to_str(r.get('T_JDONE')).upper() == "PRINTED")
                pg_is_printed = pg_status_map.get(pid)

                if pid > max_prod_id or (pg_is_printed is not None and pg_is_printed != legacy_is_printed):
                    target_prod_ids.add(pid)

            # --- IDENTIFY WHICH FORMULA RECORDS NEED SYNCING ---
            # (Standard Max ID logic for Formulas unless you want the same check for is_used)
            dbf_form_scan = dbfread.DBF(FORMULA_PRIMARY_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for r in dbf_form_scan:
                uid = _to_int(r.get('T_UID'))
                if uid and uid > max_form_id:
                    target_form_uids.add(uid)

            if not target_prod_ids and not target_form_uids:
                self.finished.emit(True, "Sync Info: No new or updated records found.")
                return

            self.progress.emit(
                f"Phase 2/3: Fetching data for {len(target_prod_ids)} prod and {len(target_form_uids)} formula records...")

            # --- DATA COLLECTION ---
            # Collect Sub-items for target IDs
            items_by_uid = collections.defaultdict(list)
            items_by_prod_id = collections.defaultdict(list)

            dbf_f_items = dbfread.DBF(FORMULA_ITEMS_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for item in dbf_f_items:
                uid = _to_int(item.get('T_UID'))
                if uid in target_form_uids:
                    items_by_uid[uid].append({
                        "uid": uid, "seq": _to_int(item.get('T_SEQ')),
                        "material_code": _to_str(item.get('T_MATCODE')),
                        "concentration": _to_float(item.get('T_CON')),
                        "is_deleted": _to_bool(item.get('T_DELETED'))
                    })

            dbf_p_items = dbfread.DBF(PRODUCTION_ITEMS_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for item in dbf_p_items:
                pid = _to_int(item.get('T_PRODID'))
                if pid in target_prod_ids:
                    items_by_prod_id[pid].append({
                        "prod_id": pid, "seq": _to_int(item.get('T_SEQ')),
                        "material_code": _to_str(item.get('T_MATCODE')),
                        "large_scale": _to_float(item.get('T_PRODA')),
                        "small_scale": _to_float(item.get('T_LABA')),
                        "total_weight": _to_float(item.get('T_WT')),
                        "total_loss": _to_float(item.get('T_LOSS')),
                        "total_consumption": _to_float(item.get('T_CONS')),
                        "is_deleted": _to_bool(item.get('T_DELETED'))
                    })

            # Fetch Primary Data for target IDs
            primary_recs = []
            dbf_primary = dbfread.DBF(FORMULA_PRIMARY_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for r in dbf_primary:
                uid = _to_int(r.get('T_UID'))
                if uid in target_form_uids:
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
                        "is_deleted": _to_bool(r.get('T_DELETED')), "is_used": _to_bool(r.get('T_USED')),
                        "matched_by": _to_str(r.get('T_MATCHBY')), "encoded_by": _to_str(r.get('T_ENCODEB')),
                        "updated_by": _to_str(r.get('T_UPDATEBY'))
                    })

            prod_recs = []
            dbf_prod = dbfread.DBF(PRODUCTION_PRIMARY_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for r in dbf_prod:
                pid = _to_int(r.get('T_PRODID'))
                if pid in target_prod_ids:
                    rem = _to_str(r.get('T_REMARKS'))
                    note_raw = _to_str(r.get('T_NOTE'))
                    note = f"{note_raw}\n{rem}".strip() if rem else note_raw
                    is_printed = (_to_str(r.get('T_JDONE')).upper() == "PRINTED")

                    prod_recs.append({
                        "prod_id": pid, "prod_date": r.get('T_PRODDATE'), "customer": _to_str(r.get('T_CUSTOMER')),
                        "form_id": _to_int(r.get('T_FID')), "index_no": _to_str(r.get('T_INDEX')),
                        "prod_code": _to_str(r.get('T_PRODCODE')), "prod_color": _to_str(r.get('T_PRODCOLO')),
                        "dosage": _to_float(r.get('T_DOSAGE')), "ld": _to_float(r.get('T_LD')),
                        "lot_no": _to_str(r.get('T_LOTNUM')), "order_no": _to_str(r.get('T_ORDERNUM')),
                        "colormatch_no": _to_str(r.get('T_CMNUM')), "colormatch_date": r.get('T_CMDATE'),
                        "mix_time": _to_str(r.get('T_MIXTIME')), "machine_no": _to_str(r.get('T_MACHINE')),
                        "note": note, "user_id": _to_str(r.get('T_USERID')), "form_type": _to_str(r.get('T_FTYPE')),
                        "inventory_c_date": r.get('T_CDATE'), "is_deleted": _to_bool(r.get('T_DELETED')),
                        "is_printed": is_printed, "prepared_by": _to_str(r.get('T_PREPARED')),
                        "encoded_by": _to_str(r.get('T_ENCODEDB')), "encoded_on": r.get('T_ENCODEDO'),
                        "conf_encoded_on": r.get('T_SDATE'), "qty_req": _to_float(r.get('T_QTYREQ')),
                        "qty_batch": _to_float(r.get('T_QTYBATCH')), "qty_prod": _to_float(r.get('T_QTYPROD'))
                    })

            # --- PHASE 3: DATABASE COMMIT ---
            self.progress.emit("Phase 3/3: Committing updates to PostgreSQL...")
            with engine.connect() as conn:
                with conn.begin():
                    # Update Formulas
                    if primary_recs:
                        conn.execute(text("""
                            INSERT INTO tbl_formula01 (form_id, index_no, date, customer, prod_code, prod_color, dosage, total_concentration, ld, mix_time, resin, application, colormatch_no, colormatch_date, notes, date_time, is_deleted, is_used)
                            VALUES (:uid, :index_no, :date, :customer, :prod_code, :prod_color, :dosage, :total_concentration, :ld, :mix_time, :resin, :application, :cm_num, :cm_date, :notes, :date_time, :is_deleted, :is_used)
                            ON CONFLICT (form_id) DO UPDATE SET 
                                is_deleted = EXCLUDED.is_deleted, is_used = EXCLUDED.is_used, notes = EXCLUDED.notes
                        """), primary_recs)

                    # Update Productions (This fixes the 'is_printed' status mismatch)
                    if prod_recs:
                        conn.execute(text("""
                            INSERT INTO tbl_production01 (prod_id, prod_date, customer, form_id, index_no, prod_code, prod_color, dosage, ld, lot_no, order_no, colormatch_no, colormatch_date, mix_time, machine_no, note, user_id, is_deleted, is_printed, inventory_c_date, form_type)
                            VALUES (:prod_id, :prod_date, :customer, :form_id, :index_no, :prod_code, :prod_color, :dosage, :ld, :lot_no, :order_no, :colormatch_no, :colormatch_date, :mix_time, :machine_no, :note, :user_id, :is_deleted, :is_printed, :inventory_c_date, :form_type)
                            ON CONFLICT (prod_id) DO UPDATE SET 
                                is_deleted = EXCLUDED.is_deleted, 
                                is_printed = EXCLUDED.is_printed,
                                note = EXCLUDED.note
                        """), prod_recs)

                        # For changed IDs, refresh their materials lists
                        pids_to_clean = list(target_prod_ids)
                        conn.execute(text("DELETE FROM tbl_production02 WHERE prod_id IN :pids"),
                                     {"pids": tuple(pids_to_clean)})

                        all_p_items = [i for pid in pids_to_clean for i in items_by_prod_id.get(pid, [])]
                        if all_p_items:
                            for item in all_p_items: item['is_deleted'] = bool(item['is_deleted'])
                            conn.execute(text("""
                                INSERT INTO tbl_production02 (prod_id, sequence_no, material_code, large_scale, small_scale, total_weight, is_deleted, total_loss, total_consumption)
                                VALUES (:prod_id, :seq, :material_code, :large_scale, :small_scale, :total_weight, :is_deleted, :total_loss, :total_consumption)
                            """), all_p_items)

            self.finished.emit(True,
                               f"Intelligent Sync complete. {len(target_prod_ids)} production and {len(target_form_uids)} formula records updated.")

        except Exception as e:
            traceback.print_exc()
            self.finished.emit(False, f"Sync Error: {e}")


class SyncRM(QObject):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)

    def run(self):
        try:
            unique_rm_codes = set()
            dbf = dbfread.DBF(RM_WH, encoding='latin1', char_decode_errors='ignore')
            for r in dbf:
                code = _to_str(r.get('T_MATCODE'))
                if _to_bool(r.get('T_DELETED')) or not code: continue
                unique_rm_codes.add(code)

            data = [{"rm_code": code} for code in unique_rm_codes]
            with engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("TRUNCATE TABLE tbl_raw_material_list RESTART IDENTITY CASCADE"))
                    conn.execute(text("INSERT INTO tbl_raw_material_list (rm_code) VALUES (:rm_code)"), data)
            self.finished.emit(True, "Warehouse sync successful.")
        except Exception as e:
            self.finished.emit(False, str(e))


def perform_rm_incoming_sync_logic(engine, progress_callback=None):
    dbf = dbfread.DBF(RM_INCOMING, encoding='latin1', char_decode_errors='ignore')
    latest_by_code = {}
    for r in dbf:
        if _to_bool(r.get('T_DELETED')): continue
        mat_code = _to_str(r.get('T_MATCODE'))
        if not mat_code: continue
        raw_date = r.get('T_DATE')
        is_valid = _is_valid_date(raw_date)
        if mat_code not in latest_by_code or (
                is_valid and (not latest_by_code[mat_code]['date'] or raw_date > latest_by_code[mat_code]['date'])):
            latest_by_code[mat_code] = {"material_code": mat_code, "note": _to_str(r.get('T_NOTE')),
                                        "date": raw_date if is_valid else None}

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