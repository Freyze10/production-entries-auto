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
RM_WH = os.path.join(DBF_BASE_PATH, 'tbl_rm_wh.dbf')

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
            with engine.connect() as conn:
                max_form_id = conn.execute(text("SELECT COALESCE(MAX(form_id), 0) FROM tbl_formula01")).scalar() or 0
                max_prod_id = conn.execute(text("SELECT COALESCE(MAX(prod_id), 0) FROM tbl_production01")).scalar() or 0

            self.progress.emit(f"Phase 1/3: Reading local items...")

            items_by_uid = collections.defaultdict(list)
            new_uids = set()

            items_by_prod_id = collections.defaultdict(list)
            new_prod_ids = set()

            production_items = dbfread.DBF(PRODUCTION_ITEMS_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            dbf_items = dbfread.DBF(FORMULA_ITEMS_DBF_PATH, encoding='latin1', char_decode_errors='ignore')

            for item_rec in dbf_items:
                uid = _to_int(item_rec.get('T_UID'))
                # if uid is None or uid <= max_uid: continue
                if uid is None or uid <= max_form_id:
                    continue
                new_uids.add(uid)
                items_by_uid[uid].append({
                    "uid": uid, "seq": _to_int(item_rec.get('T_SEQ')),
                    "material_code": str(item_rec.get('T_MATCODE', '') or '').strip(),
                    "concentration": _to_float(item_rec.get('T_CON')),
                    "is_deleted": str(item_rec.get('T_DELETED', '') or '').strip()
                })

            for item_rec in production_items:
                # Skip deleted records
                prod_id = _to_int(item_rec.get('T_PRODID'))
                if prod_id is None or prod_id <= max_prod_id:
                    continue

                new_prod_ids.add(prod_id)

                # Extract item data (excluding t_prodb and t_labb as requested)
                items_by_prod_id[prod_id].append({
                    "prod_id": prod_id,
                    "lot_num": str(item_rec.get('T_LOTNUM', '') or '').strip(),
                    "confirmation_date": item_rec.get('T_CDATE'),  # confirmation date
                    "production_date": item_rec.get('T_PRODDATE'),  # production date
                    "seq": _to_int(item_rec.get('T_SEQ')),
                    "material_code": str(item_rec.get('T_MATCODE', '') or '').strip(),
                    "large_scale": _to_float(item_rec.get('T_PRODA')),  # Large scale (KG)
                    "small_scale": _to_float(item_rec.get('T_LABA')),  # Small scale (G)
                    # t_prodb and t_labb are intentionally excluded
                    "is_deleted": str(item_rec.get('T_DELETED', '') or '').strip(),
                    "total_weight": _to_float(item_rec.get('T_WT')),  # Total weight
                    "total_loss": _to_float(item_rec.get('T_LOSS')),  # Total loss
                    "total_consumption": _to_float(item_rec.get('T_CONS'))  # Total consumption
                })



            self.progress.emit(f"Phase 1/3: Found {len(items_by_uid)} groups of new active items.")

            self.progress.emit("Phase 2/3: Reading Production data...")
            prod_recs = []
            primary_recs = []
            dbf_prod = dbfread.DBF(PRODUCTION_PRIMARY_DBF_PATH, encoding='latin1', char_decode_errors='ignore')
            dbf_primary = dbfread.DBF(FORMULA_PRIMARY_DBF_PATH, encoding='latin1', char_decode_errors='ignore')

            for r in dbf_primary:
                uid = _to_int(r.get('T_UID'))
                if uid is None or uid <= max_form_id:
                    continue
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
                    "is_deleted": str(r.get('T_DELETED', '')),
                    "dbf_updated_by": str(r.get('T_UPDATEBY', '') or '').strip(),
                    "dbf_updated_on_text": dbf_updated_on
                })

            for r in dbf_prod:
                # Skip deleted records
                prod_id = _to_int(r.get('T_PRODID'))
                if prod_id is None or prod_id <= max_prod_id:
                    continue
                formula_id = _to_int(r.get('T_FID'))
                if formula_id is None or formula_id == 0:
                    continue
                # Concatenate remarks and notes
                remarks = str(r.get('T_REMARKS', '') or '').strip()
                notes_raw = str(r.get('T_NOTE', '') or '').strip()
                note = f"{notes_raw}\n{remarks}".strip() if remarks else notes_raw

                # is_printed: "PRINTED" → True, else False
                jdone_raw = str(r.get('T_JDONE', '') or '').strip().upper()
                is_printed = jdone_raw == "PRINTED"
                prod_recs.append({
                    "prod_id": prod_id,
                    "production_date": r.get('T_PRODDATE'),
                    "customer": str(r.get('T_CUSTOMER', '') or '').strip(),
                    "formulation_id": formula_id,
                    "formula_index": str(r.get('T_INDEX', '') or '').strip(),
                    "product_code": str(r.get('T_PRODCODE', '') or '').strip(),
                    "product_color": str(r.get('T_PRODCOLO', '') or '').strip(),
                    "dosage": _to_float(r.get('T_DOSAGE')),
                    "ld_percent": _to_float(r.get('T_LD')),
                    "lot_number": str(r.get('T_LOTNUM', '') or '').strip(),
                    "order_form_no": str(r.get('T_ORDERNUM', '') or '').strip(),
                    "colormatch_no": str(r.get('T_CMNUM', '') or '').strip(),
                    "colormatch_date": r.get('T_CMDATE'),
                    "mixing_time": str(r.get('T_MIXTIME', '') or '').strip(),
                    "machine_no": str(r.get('T_MACHINE', '') or '').strip(),
                    "qty_required": _to_float(r.get('T_QTYREQ')),
                    "qty_per_batch": _to_float(r.get('T_QTYBATCH')),
                    "qty_produced": _to_float(r.get('T_QTYPROD')),
                    "note": note,
                    "user_id": str(r.get('T_USERID', '') or '').strip(),
                    "prepared_by": str(r.get('T_PREPARED', '') or '').strip(),
                    "encoded_by": str(r.get('T_ENCODEDB', '') or '').strip(),
                    "encoded_on": r.get('T_ENCODEDO'),
                    "is_deleted": str(r.get('T_DELETED', '')),
                    "is_printed": is_printed,
                    "confirmation_date": r.get('T_CDATE'),
                    "scheduled_date": r.get('T_SDATE'),
                    "form_type": str(r.get('T_FTYPE', '') or '').strip()
                })

            self.progress.emit(f"Phase 2/3: Found new valid records.")

            if not prod_recs:
                self.finished.emit(True, f"Sync Info: No new records found to sync."); return

            all_items_to_insert = [item for rec in primary_recs for item in items_by_uid.get(rec['uid'], [])]
            all_prod_items_to_insert = [
                item
                for rec in prod_recs
                for item in items_by_prod_id.get(rec['prod_id'], [])
            ]

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

                    # Production sync
                    conn.execute(text("""
                        INSERT INTO tbl_production01 (
                            prod_id, prod_date, customer, form_id, index_no,
                            prod_code, prod_color, dosage, ld, lot_no,
                            order_no, colormatch_no, colormatch_date, mix_time, machine_no,
                            note, user_id, is_deleted, is_printed, inventory_c_date, form_type
                        )
                        VALUES (
                            :prod_id, :production_date, :customer, :formulation_id, :formula_index,
                            :product_code, :product_color, :dosage, :ld_percent, :lot_number,
                            :order_form_no, :colormatch_no, :colormatch_date, :mixing_time, :machine_no,
                            :note, :user_id, :is_deleted, :is_printed, :confirmation_date, :form_type
                        )
                        ON CONFLICT (prod_id) DO UPDATE SET
                            prod_date = EXCLUDED.prod_date,
                            customer = EXCLUDED.customer,
                            form_id = EXCLUDED.form_id,
                            index_no = EXCLUDED.index_no,
                            prod_code = EXCLUDED.prod_code,
                            prod_color = EXCLUDED.prod_color,
                            dosage = EXCLUDED.dosage,
                            ld = EXCLUDED.ld,
                            lot_no = EXCLUDED.lot_no,
                            order_no = EXCLUDED.order_no,
                            colormatch_no = EXCLUDED.colormatch_no,
                            colormatch_date = EXCLUDED.colormatch_date,
                            mix_time = EXCLUDED.mix_time,
                            machine_no = EXCLUDED.machine_no,
                            note = EXCLUDED.note,
                            user_id = EXCLUDED.user_id,
                            is_deleted = EXCLUDED.is_deleted,
                            is_printed = EXCLUDED.is_printed,
                            inventory_c_date = EXCLUDED.inventory_c_date,
                            form_type = EXCLUDED.form_type
                    """), prod_recs)

                    conn.execute(text("""
                        INSERT INTO tbl_production_encode (
                            prod_id, prepared_by, encoded_by, encoded_on, confirmation_encoded_on
                        )
                        VALUES (
                            :prod_id, :prepared_by, :encoded_by, :encoded_on, :scheduled_date
                        )
                    """), prod_recs)

                    conn.execute(text("""
                        INSERT INTO tbl_production_quantity (
                                prod_id, quantity_req , quantity_batch, quantity_prod
                        )
                        VALUES (
                            :prod_id, :qty_required, :qty_per_batch, :qty_produced
                        )
                    """), prod_recs)

                    # Insert production items (materials)
                    if all_prod_items_to_insert:
                        conn.execute(text("""
                            INSERT INTO tbl_production02 (
                                prod_id, sequence_no, material_code, large_scale, small_scale, total_weight, is_deleted,
                                total_loss, total_consumption
                            )
                            VALUES (
                                :prod_id, :seq, :material_code, :large_scale, 
                                :small_scale, :total_weight, :is_deleted,
                                :total_loss, :total_consumption
                            )ON CONFLICT DO NOTHING
                        """), all_prod_items_to_insert)

            self.finished.emit(True,
                               f"Production sync complete.\n new records items processed.")
        except dbfread.DBFNotFound as e:
            self.finished.emit(False, f"File Not Found: A required formula DBF file is missing.\nDetails: {e}")
        except Exception as e:
            trace_info = traceback.format_exc();
            print(f"FORMULA SYNC CRITICAL ERROR: {e}\n{trace_info}")
            self.finished.emit(False, f"An unexpected error occurred during formula sync:\n{e}")


class SyncRM(QObject):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)

    def run(self):
        try:
            self.progress.emit("Reading warehouse data...")

            # Use a set to store unique RM codes
            unique_rm_codes = set()
            dbf = dbfread.DBF(RM_WH, encoding='latin1', char_decode_errors='ignore')

            for r in dbf:
                # Skip deleted or empty records
                if r.get('T_DELETED') or not str(r.get('T_MATCODE', '')).strip():
                    continue

                unique_rm_codes.add(str(r.get('T_MATCODE')).strip())

            if not unique_rm_codes:
                self.finished.emit(True, "No records found to sync.")
                return

            # Prepare data for SQLAlchemy (list of dicts)
            data = [{"rm_code": code} for code in unique_rm_codes]

            self.progress.emit(f"Updating database with {len(data)} materials...")
            with engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("TRUNCATE TABLE tbl_raw_material_list RESTART IDENTITY"))
                    conn.execute(text("INSERT INTO tbl_raw_material_list (rm_code) VALUES (:rm_code)"), data)

            self.finished.emit(True, f"Sync complete. {len(data)} materials updated.")

        except Exception as e:
            print(f"RM SYNC ERROR: {e}")
            self.finished.emit(False, str(e))