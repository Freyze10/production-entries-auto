import collections
import os
import traceback

import dbfread
import sqlalchemy
from PyQt6.QtCore import pyqtSignal, QObject
from sqlalchemy import text, create_engine

DB_CONFIG = {"host": "192.168.1.13", "port": 5432, "dbname": "db_formula", "user": "postgres", "password": "mbpi"}
DBF_BASE_PATH = r'\\system-server\SYSTEM-NEW-OLD'
CUSTOMER_DBF_PATH = os.path.join(DBF_BASE_PATH, 'tbl_customer01.dbf')
FORMULA_PRIMARY_DBF_PATH = os.path.join(DBF_BASE_PATH, 'tbl_formula01.dbf')
FORMULA_ITEMS_DBF_PATH = os.path.join(DBF_BASE_PATH, 'tbl_formula02.dbf')
PRODUCTION_PRIMARY_DBF_PATH = os.path.join(DBF_BASE_PATH, 'tbl_prod01.dbf')
PRODUCTION_ITEMS_DBF_PATH = os.path.join(DBF_BASE_PATH, 'tbl_prod02.dbf')

try:
    db_url = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=3600)
except Exception as e:
    print(f"CRITICAL: Could not create database engine. Error: {e}")

def _to_float(value, default=None):
    if value is None: return default
    if isinstance(value, bytes) and value.strip(b'\x00') == b'': return default
    try:
        return float(value)
    except (ValueError, TypeError):
        try:
            cleaned_value = str(value).strip().replace('\x00', '')
            return float(cleaned_value) if cleaned_value else default
        except (ValueError, TypeError):
            return default

def _to_int(value, default=None):
    if value is None: return default
    if isinstance(value, bytes) and value.strip(b'\x00') == b'': return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        try:
            cleaned_value = str(value).strip().replace('\x00', '')
            return int(float(cleaned_value)) if cleaned_value else default
        except (ValueError, TypeError):
            return default





class SyncFormulaWorker(QObject):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)

    def run(self):
        try:
            self.progress.emit(f"Phase 1/3: Reading local formula items...")
            items_by_uid = collections.defaultdict(list)
            new_uids = set()
            dbf_items = dbfread.DBF(FORMULA_ITEMS_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for item_rec in dbf_items:
                uid = _to_int(item_rec.get('T_UID'))
                new_uids.add(uid)
                items_by_uid[uid].append({
                    "uid": uid, "seq": _to_int(item_rec.get('T_SEQ')),
                    "material_code": str(item_rec.get('T_MATCODE', '') or '').strip(),
                    "concentration": _to_float(item_rec.get('T_CON')),
                    "update_by": str(item_rec.get('T_UPDATEBY', '') or '').strip(),
                    "update_on_text": str(item_rec.get('T_UDATE', '') or '').strip()
                })
            self.progress.emit(f"Phase 1/3: Found {len(items_by_uid)} groups of new active items.")

            self.progress.emit("Phase 2/3: Reading Formula data...")
            primary_recs = []
            dbf_primary = dbfread.DBF(FORMULA_PRIMARY_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for row_num, r in enumerate(dbf_primary, start=1):
                uid = _to_int(r.get('T_UID'))
                primary_recs.append({
                    "row_num" : row_num,
                    "formula_index": str(r.get('T_INDEX', '') or '').strip(), "uid": uid,
                    "formula_date": r.get('T_DATE'),
                    "customer": str(r.get('T_CUSTOMER', '') or '').strip(),
                    "product_code": str(r.get('T_PRODCODE', '') or '').strip(),
                    "product_color": str(r.get('T_PRODCOLO', '') or '').strip(), "dosage": _to_float(r.get('T_DOSAGE')),
                    "ld": _to_float(r.get('T_LD')),
                    "mix_type": str(r.get('T_MIX', '') or '').strip(), "resin": str(r.get('T_RESIN', '') or '').strip(),
                    "application": str(r.get('T_APP', '') or '').strip(),
                    "cm_num": str(r.get('T_CMNUM', '') or '').strip(), "cm_date": r.get('T_CMDATE'),
                    "matched_by": str(r.get('T_MATCHBY', '') or '').strip(),
                    "encoded_by": str(r.get('T_ENCODEB', '') or '').strip(),
                    "remarks": str(r.get('T_REM', '') or '').strip(),
                    "total_concentration": _to_float(r.get('T_TOTALCON')), "is_used": bool(r.get('T_USED')),
                    "dbf_updated_by": str(r.get('T_UPDATEBY', '') or '').strip(),
                    "dbf_updated_on_text": str(r.get('T_UDATE', '') or '').strip(),
                })

            self.progress.emit(f"Phase 2/3: Found {len(primary_recs)} new valid records.")
            if not primary_recs: self.finished.emit(True,
                                                    f"Sync Info: No new formula records found to sync."); return

            all_items_to_insert = [item for rec in primary_recs for item in items_by_uid.get(rec['uid'], [])]

            self.progress.emit("Phase 3/3: Syncing Data...")
            with engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("""
                        INSERT INTO tbl_formula_encode (
                            encode_id, match_by, encoded_by, updated_by
                        )
                        VALUES (
                             :row_num, :matched_by, :encoded_by, :dbf_updated_by
                        )
                        ON CONFLICT (uid) DO UPDATE SET
                            encoded_id = EXCLUDED.encoded_id,
                            matched_by = EXCLUDED.matched_by,
                            encoded_by = EXCLUDED.encoded_by,
                            dbf_updated_by = EXCLUDED.dbf_updated_by,
                    """), primary_recs)


                    conn.execute(text("""
                        INSERT INTO tbl_formula01 (
                            formula_index, uid, formula_date, customer, product_code, product_color, dosage, ld,
                            mix_type, resin, application, cm_num, cm_date, matched_by, encoded_by, remarks,
                            total_concentration, is_used, dbf_updated_by, dbf_updated_on_text, last_synced_on
                        )
                        VALUES (
                            :formula_index, :uid, :formula_date, :customer, :product_code, :product_color, :dosage, :ld,
                            :mix_type, :resin, :application, :cm_num, :cm_date, :matched_by, :encoded_by, :remarks,
                            :total_concentration, :is_used, :dbf_updated_by, :dbf_updated_on_text, NOW()
                        )
                        ON CONFLICT (uid) DO UPDATE SET
                            formula_index = EXCLUDED.formula_index,
                            formula_date = EXCLUDED.formula_date,
                            customer = EXCLUDED.customer,
                            product_code = EXCLUDED.product_code,
                            product_color = EXCLUDED.product_color,
                            dosage = EXCLUDED.dosage,
                            ld = EXCLUDED.ld,
                            mix_type = EXCLUDED.mix_type,
                            resin = EXCLUDED.resin,
                            application = EXCLUDED.application,
                            cm_num = EXCLUDED.cm_num,
                            cm_date = EXCLUDED.cm_date,
                            matched_by = EXCLUDED.matched_by,
                            encoded_by = EXCLUDED.encoded_by,
                            remarks = EXCLUDED.remarks,
                            total_concentration = EXCLUDED.total_concentration,
                            is_used = EXCLUDED.is_used,
                            dbf_updated_by = EXCLUDED.dbf_updated_by,
                            dbf_updated_on_text = EXCLUDED.dbf_updated_on_text,
                            last_synced_on = NOW();
                    """), primary_recs)
                    if all_items_to_insert:
                        conn.execute(text("""
                            INSERT INTO formula_items (uid, seq, material_code, concentration, update_by, update_on_text)
                            VALUES (:uid, :seq, :material_code, :concentration, :update_by, :update_on_text);
                        """), all_items_to_insert)
            self.finished.emit(True,
                               f"Formula sync complete.\n{len(primary_recs)} new primary records and {len(all_items_to_insert)} items processed.")
        except dbfread.DBFNotFound as e:
            self.finished.emit(False, f"File Not Found: A required formula DBF file is missing.\nDetails: {e}")
        except Exception as e:
            trace_info = traceback.format_exc();
            print(f"FORMULA SYNC CRITICAL ERROR: {e}\n{trace_info}")
            self.finished.emit(False, f"An unexpected error occurred during formula sync:\n{e}")
