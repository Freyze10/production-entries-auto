import collections
import os
import traceback

import dbfread
import sqlalchemy
from PyQt6.QtCore import pyqtSignal, QObject
from sqlalchemy import text, create_engine

DB_CONFIG = {"host": "localhost", "port": 5433, "dbname": "db_production", "user": "postgres", "password": "password"}
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





class Sync(QObject):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)

    def run(self):
        try:
            with engine.begin() as conn:
                self.progress.emit("Reading customer data...")

                dbf_customer = dbfread.DBF(CUSTOMER_DBF_PATH, encoding='latin1', char_decode_errors='ignore')

                primary_cust = []

                for r in dbf_customer:
                    if bool(r.get('T_DELETED', False)):
                        continue

                    cust_id_str = str(r.get('T_CUSTID', '') or '').strip()

                    try:
                        cust_id = int(cust_id_str)
                    except:
                        print(f"Invalid ID: {cust_id_str}")
                        continue

                    customer_name = str(r.get('T_CUSTOMER', '') or '').strip()

                    primary_cust.append({
                        "customer_id": cust_id,
                        "customer_name": customer_name
                    })

                if not primary_cust:
                    self.finished.emit(True, "No records found.")
                    return

                self.progress.emit(f"Syncing {len(primary_cust)} records...")

                conn.execute(text("""
                    INSERT INTO tbl_customer (customer_id, customer_name)
                    VALUES (:customer_id, :customer_name)
                    ON CONFLICT (customer_id) DO UPDATE SET
                        customer_name = EXCLUDED.customer_name
                """), primary_cust)
        except dbfread.DBFNotFound as e:
            self.finished.emit(False, f"File Not Found: A required Customer DBF file is missing.\nDetails: {e}")
        except Exception as e:
            trace_info = traceback.format_exc();
            print(f"CUSTOMER SYNC CRITICAL ERROR: {e}\n{trace_info}")
            self.finished.emit(False, f"An unexpected error occurred during customer sync:\n{e}")


        try:
            # with engine.connect() as conn:
            #     max_uid = conn.execute(text("SELECT COALESCE(MAX(uid), 0) FROM formula_primary")).scalar()
            self.progress.emit(f"Phase 1/3: Reading local formula items...")
            items_by_uid = collections.defaultdict(list)
            new_uids = set()
            dbf_items = dbfread.DBF(FORMULA_ITEMS_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for item_rec in dbf_items:
                uid = _to_int(item_rec.get('T_UID'))
                # if uid is None or uid <= max_uid: continue
                new_uids.add(uid)
                items_by_uid[uid].append({
                    "uid": uid, "seq": _to_int(item_rec.get('T_SEQ')),
                    "material_code": str(item_rec.get('T_MATCODE', '') or '').strip(),
                    "concentration": _to_float(item_rec.get('T_CON')),
                    "is_deleted": str(item_rec.get('T_DELETED', '') or '').strip()
                })
            self.progress.emit(f"Phase 1/3: Found {len(items_by_uid)} groups of new active items.")

            self.progress.emit("Phase 2/3: Reading Formula data...")
            primary_recs = []
            dbf_primary = dbfread.DBF(FORMULA_PRIMARY_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            for r in dbf_primary:
                ### CHANGE: Skip T_DELETED records ###
                # if bool(r.get('T_DELETED', False)):
                #     continue
                uid = _to_int(r.get('T_UID'))
                # if uid is None or uid <= max_uid: continue
                dbf_updated_on_text = str(r.get('T_UDATE', '') or '').strip()
                cm_date = str(r.get('T_CMDATE', '') or '').strip()
                # If empty → set to None
                dbf_updated_on = None if not dbf_updated_on_text else dbf_updated_on_text
                colormatch_date = None if not cm_date else cm_date
                primary_recs.append({
                    "formula_index": str(r.get('T_INDEX', '') or '').strip(), "uid": uid,
                    "formula_date": r.get('T_DATE'),
                    "customer": str(r.get('T_CUSTOMER', '') or '').strip(),
                    "product_code": str(r.get('T_PRODCODE', '') or '').strip(),
                    "product_color": str(r.get('T_PRODCOLO', '') or '').strip(), "dosage": _to_float(r.get('T_DOSAGE')),
                    "ld": _to_float(r.get('T_LD')),
                    "mix_type": str(r.get('T_MIX', '') or '').strip(), "resin": str(r.get('T_RESIN', '') or '').strip(),
                    "application": str(r.get('T_APP', '') or '').strip(),
                    "cm_num": str(r.get('T_CMNUM', '') or '').strip(),
                    "cm_date": colormatch_date,
                    "matched_by": str(r.get('T_MATCHBY', '') or '').strip(),
                    "encoded_by": str(r.get('T_ENCODEB', '') or '').strip(),
                    "remarks": str(r.get('T_REM', '') or '').strip(),
                    "total_concentration": _to_float(r.get('T_TOTALCON')), "is_used": bool(r.get('T_USED')),
                    "is_deleted": str(r.get('T_DELETED', '') or '').strip(),
                    "dbf_updated_by": str(r.get('T_UPDATEBY', '') or '').strip(),
                    "dbf_updated_on_text": dbf_updated_on
                })

            self.progress.emit(f"Phase 2/3: Found {len(primary_recs)} new valid records.")
            if not primary_recs: self.finished.emit(True,
                                                    f"Sync Info: No new formula records found to sync."); return

            all_items_to_insert = [item for rec in primary_recs for item in items_by_uid.get(rec['uid'], [])]

            self.progress.emit("Phase 3/3: Syncing Data...")
            with engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("""
                        INSERT INTO tbl_formula01 (
                            form_id, index_no, date, customer, prod_code, prod_color, dosage, total_concentration, ld, 
                            mix_time, resin, application, colormatch_no, colormatch_date, notes,
                            date_time, is_deleted, is_used
                        )
                        VALUES (
                            :uid, :formula_index, :formula_date, 1, :product_code, :product_color, :dosage, :total_concentration,
                            :ld, :mix_type, :resin, :application, :cm_num, :cm_date, :remarks, :dbf_updated_on_text, :is_deleted,
                            :is_used
                        )
                        ON CONFLICT (form_id) DO UPDATE SET
                            index_no = EXCLUDED.index_no,
                            date = EXCLUDED.date,
                            customer = EXCLUDED.customer,
                            prod_code = EXCLUDED.prod_code,
                            prod_color = EXCLUDED.prod_color,
                            dosage = EXCLUDED.dosage,
                            ld = EXCLUDED.ld,
                            mix_time = EXCLUDED.mix_time,
                            resin = EXCLUDED.resin,
                            application = EXCLUDED.application,
                            colormatch_no = EXCLUDED.colormatch_no,
                            colormatch_date = EXCLUDED.colormatch_date,
                            notes = EXCLUDED.notes,
                            total_concentration = EXCLUDED.total_concentration,
                            is_deleted = EXCLUDED.is_deleted,
                            is_used = EXCLUDED.is_used,
                            date_time = EXCLUDED.date_time
                    """), primary_recs)

                    conn.execute(text("""
                        INSERT INTO tbl_formula_encode (
                            form_id, match_by, encoded_by, updated_by
                        )
                        VALUES (
                             :uid, :matched_by, :encoded_by, :dbf_updated_by
                        )
                    """), primary_recs)

                    if all_items_to_insert:
                        conn.execute(text("""
                            INSERT INTO tbl_formula02 (form_id, sequence_no, material_code, concentration, is_deleted)
                            VALUES (:uid, :seq, :material_code, :concentration, :is_deleted);
                        """), all_items_to_insert)
            self.finished.emit(True,
                               f"Formula sync complete.\n{len(primary_recs)} new primary records and {len(all_items_to_insert)} items processed.")
        except dbfread.DBFNotFound as e:
            self.finished.emit(False, f"File Not Found: A required formula DBF file is missing.\nDetails: {e}")
        except Exception as e:
            trace_info = traceback.format_exc();
            print(f"FORMULA SYNC CRITICAL ERROR: {e}\n{trace_info}")
            self.finished.emit(False, f"An unexpected error occurred during formula sync:\n{e}")
