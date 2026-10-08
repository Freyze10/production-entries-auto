from db.connection import get_connection
from datetime import datetime

from workstation.workstation_details import _get_workstation_info


def create_current_user(workstation):
    con = get_connection()
    cursor = con.cursor()

    hostname = workstation['h']
    ip_address = workstation['i']
    mac_address = workstation['m']
    username = "User"
    role_id = 3
    password = "mbpi"

    cursor.execute("""
        INSERT INTO tbl_user (role_id, hostname, ip_address, mac_address, username, password)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (role_id, hostname, ip_address, mac_address, username, password))

    con.commit()
    cursor.close()
    con.close()


def update_user_workstation(mac, new_host, new_ip):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE tbl_user 
            SET hostname = %s, ip_address = %s 
            WHERE mac_address = %s
        """, (new_host, new_ip, mac))
        conn.commit()
    except Exception as e:
        print(f"Error updating workstation: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def save_user_changes(user_id, data):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            UPDATE tbl_user 
            SET 
                username = %s, 
                hostname = %s, 
                password = %s, 
                ip_address = %s, 
                mac_address = %s, 
                role_id = %s
            WHERE user_id = %s;
        """

        cursor.execute(query, (
            data['username'],
            data['hostname'],
            data['password'],
            data['ip'],
            data['mac'],
            data['role_id'],
            user_id
        ))

        conn.commit()
        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"Error in save_user_changes: {e}")
        return False


def log_audit_trail(mac_address: str, action_type: str, details: str):
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Step 1: Get user_id using mac_address
        cur.execute("""
            SELECT user_id 
            FROM tbl_user 
            WHERE mac_address = %s 
            LIMIT 1
        """, (mac_address,))

        result = cur.fetchone()

        if not result:
            print(f"⚠️ Warning: No user found with MAC address {mac_address}")
            user_id = None
        else:
            user_id = result[0]

        # Step 2: Insert into audit trail
        cur.execute("""
            INSERT INTO tbl_audit_trail 
                (timestamp, user_id, action_type, details)
            VALUES 
                (NOW(), %s, %s, %s)
        """, (user_id, action_type, details))

        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"❌ Error logging audit trail: {e}")

    finally:
        cur.close()
        conn.close()


def add_new_role(name, dept):
    """Adds a new row to the tbl_role table."""
    try:
        conn = get_connection()
        cur = conn.cursor()

        query = "INSERT INTO tbl_role (role, department) VALUES (%s, %s)"
        cur.execute(query, (name.upper(), dept))

        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error add_new_role: {e}")
        return False


def save_production_record(header, quantity, encode, materials, is_update=False):
    """
    Saves or Updates a complete production record across 4 tables, supporting separators.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if is_update:
            # 1. Update Header
            cursor.execute("""
                UPDATE tbl_production01 SET 
                    prod_date=%s, customer=%s, form_id=%s, index_no=%s, prod_code=%s, 
                    prod_color=%s, dosage=%s, ld=%s, lot_no=%s, order_no=%s, 
                    mix_time=%s, machine_no=%s, note=%s, inventory_c_date=%s, form_type=%s
                WHERE prod_id = %s
            """, (header['prod_date'], header['customer'], header['form_id'], header['index_no'],
                  header['prod_code'], header['prod_color'], header['dosage'], header['ld'],
                  header['lot_no'], header['order_no'], header['mix_time'], header['machine_no'],
                  header['note'], header['inventory_c_date'], header['form_type'], header['prod_id']))

            # 2. Update Quantity
            cursor.execute("""
                UPDATE tbl_production_quantity SET 
                    quantity_req=%s, quantity_batch=%s, quantity_prod=%s
                WHERE prod_id = %s
            """, (quantity['req'], quantity['batch'], quantity['prod'], header['prod_id']))

            # 3. Update Encode
            cursor.execute("""
                UPDATE tbl_production_encode SET prepared_by=%s WHERE prod_id = %s
            """, (encode['prepared_by'], header['prod_id']))

            # 4. Refresh Materials (Delete old, Insert new including separators)
            cursor.execute("DELETE FROM tbl_production02 WHERE prod_id = %s", (header['prod_id'],))

        else:
            # --- INSERT MODE ---
            cursor.execute("""
                INSERT INTO tbl_production01 (
                    prod_id, prod_date, customer, form_id, index_no, prod_code, prod_color, 
                    dosage, ld, lot_no, order_no, mix_time, machine_no, note, 
                    user_id, inventory_c_date, form_type, is_deleted, is_printed
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE, FALSE)
            """, (header['prod_id'], header['prod_date'], header['customer'], header['form_id'],
                  header['index_no'], header['prod_code'], header['prod_color'], header['dosage'],
                  header['ld'], header['lot_no'], header['order_no'], header['mix_time'],
                  header['machine_no'], header['note'], header['user_id'], header['inventory_c_date'],
                  header['form_type']))

            cursor.execute("""
                INSERT INTO tbl_production_quantity (prod_id, quantity_req, quantity_batch, quantity_prod)
                VALUES (%s, %s, %s, %s)
            """, (header['prod_id'], quantity['req'], quantity['batch'], quantity['prod']))

            cursor.execute("""
                INSERT INTO tbl_production_encode (prod_id, prepared_by, encoded_by, encoded_on)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            """, (header['prod_id'], encode['prepared_by'], encode['encoded_by']))

        # 5. Insert Materials & Separators (Maintains sequence numbers completely)
        material_query = """
            INSERT INTO tbl_production02 (prod_id, sequence_no, material_code, large_scale, small_scale, total_weight, is_deleted)
            VALUES (%s, %s, %s, %s, %s, %s, FALSE)
        """
        cursor.executemany(material_query, materials)

        conn.commit()
        return True, "Success"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()


import re


def save_manual_production_record(header, quantity, encode, materials, is_update=False, non_raw_payloads=None):
    """
    Saves or Updates a complete production record using an intelligent upsert/sync strategy
    for tbl_production02 and normalizes tbl_production03_detail fields.
    """
    if non_raw_payloads is None:
        non_raw_payloads = {}

    conn = get_connection()
    cursor = conn.cursor()
    try:
        workstation = _get_workstation_info()
        user_full_name = workstation['u']  # format: hostname\username

        if is_update:
            # 1. Update Header
            cursor.execute("""
                UPDATE tbl_production01 SET 
                    prod_date=%s, customer=%s, form_id=%s, index_no=%s, prod_code=%s, 
                    prod_color=%s, dosage=%s, ld=%s, lot_no=%s, order_no=%s, 
                    mix_time=%s, machine_no=%s, note=%s, inventory_c_date=%s, form_type=%s
                WHERE prod_id = %s
            """, (header['prod_date'], header['customer'], header['form_id'], header['index_no'],
                  header['prod_code'], header['prod_color'], header['dosage'], header['ld'],
                  header['lot_no'], header['order_no'], header['mix_time'], header['machine_no'],
                  header['note'], header['inventory_c_date'], header['form_type'], header['prod_id']))

            # 2. Update Quantity
            cursor.execute("""
                UPDATE tbl_production_quantity SET 
                    quantity_req=%s, quantity_batch=%s, quantity_prod=%s
                WHERE prod_id = %s
            """, (quantity['req'], quantity['batch'], quantity['prod'], header['prod_id']))

            # 3. Update Encode
            cursor.execute("""
                UPDATE tbl_production_encode SET prepared_by=%s WHERE prod_id = %s
            """, (encode['prepared_by'], header['prod_id']))

            # 4. INTELLIGENT MATERIALS SYNC
            incoming_sequences = [mat[1] for mat in materials]

            if incoming_sequences:
                cursor.execute("""
                    DELETE FROM tbl_production02 
                    WHERE prod_id = %s AND sequence_no NOT IN %s
                """, (header['prod_id'], tuple(incoming_sequences)))
            else:
                cursor.execute("DELETE FROM tbl_production02 WHERE prod_id = %s", (header['prod_id'],))

        else:
            # --- INSERT MODE ---
            cursor.execute("""
                INSERT INTO tbl_production01 (
                    prod_id, prod_date, customer, form_id, index_no, prod_code, prod_color, 
                    dosage, ld, lot_no, order_no, mix_time, machine_no, note, 
                    user_id, inventory_c_date, form_type, is_deleted, is_printed
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE, FALSE)
            """, (header['prod_id'], header['prod_date'], header['customer'], header['form_id'],
                  header['index_no'], header['prod_code'], header['prod_color'], header['dosage'],
                  header['ld'], header['lot_no'], header['order_no'], header['mix_time'],
                  header['machine_no'], header['note'], header['user_id'], header['inventory_c_date'],
                  header['form_type']))

            cursor.execute("""
                INSERT INTO tbl_production_quantity (prod_id, quantity_req, quantity_batch, quantity_prod)
                VALUES (%s, %s, %s, %s)
            """, (header['prod_id'], quantity['req'], quantity['batch'], quantity['prod']))

            cursor.execute("""
                INSERT INTO tbl_production_encode (prod_id, prepared_by, encoded_by, encoded_on)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            """, (header['prod_id'], encode['prepared_by'], encode['encoded_by']))

        # 5. UPSERT Materials & Separators into tbl_production02
        for mat in materials:
            cursor.execute("""
                INSERT INTO tbl_production02 (prod_id, sequence_no, material_code, large_scale, small_scale, total_weight, is_deleted)
                VALUES (%s, %s, %s, %s, %s, %s, FALSE)
                ON CONFLICT (prod_id, sequence_no) DO UPDATE SET 
                    material_code = EXCLUDED.material_code,
                    large_scale = EXCLUDED.large_scale,
                    small_scale = EXCLUDED.small_scale,
                    total_weight = EXCLUDED.total_weight,
                    is_deleted = FALSE
                RETURNING id;
            """, (mat[0], mat[1], mat[2], mat[3], mat[4], mat[5]))

            prod02_id = cursor.fetchone()[0]
            mat_code = mat[2]

            # 6. Handle production03 breakdowns for Non-Raw materials
            if mat_code in non_raw_payloads:
                payload = non_raw_payloads[mat_code]
                source_deductions = payload.get("source_deductions", [])
                change_reason = payload.get("change_reason", "")

                if source_deductions:
                    cursor.execute("""
                        SELECT id, version_no, created_at, created_by 
                        FROM tbl_production03_header 
                        WHERE production02_id = %s AND is_cancelled = FALSE
                    """, (prod02_id,))
                    active_header = cursor.fetchone()

                    if active_header and is_update and change_reason:
                        old_header_id = active_header[0]
                        old_version = active_header[1]
                        original_created_at = active_header[2]
                        original_created_by = active_header[3]

                        cursor.execute("""
                            UPDATE tbl_production03_header 
                            SET is_cancelled = TRUE, 
                                cancel_reason = %s, 
                                updated_at = CURRENT_TIMESTAMP, 
                                modified_by = %s 
                            WHERE id = %s
                        """, (change_reason, user_full_name, old_header_id))

                        cursor.execute("""
                            INSERT INTO tbl_production03_header (
                                production02_id, version_no, created_at, updated_at, 
                                created_by, modified_by, is_cancelled, cancel_reason
                            ) VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s, %s, FALSE, NULL)
                            RETURNING id;
                        """, (prod02_id, old_version + 1, original_created_at, original_created_by, user_full_name))
                        header_03_id = cursor.fetchone()[0]

                    elif active_header:
                        header_03_id = active_header[0]
                        cursor.execute("""
                            UPDATE tbl_production03_header 
                            SET updated_at = CURRENT_TIMESTAMP, modified_by = %s 
                            WHERE id = %s
                        """, (user_full_name, header_03_id))

                        cursor.execute("""
                            DELETE FROM tbl_production03_detail WHERE production03_header_id = %s
                        """, (header_03_id,))
                    else:
                        cursor.execute("""
                            INSERT INTO tbl_production03_header (
                                production02_id, version_no, created_at, updated_at, 
                                created_by, modified_by, is_cancelled, cancel_reason
                            ) VALUES (%s, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s, %s, FALSE, NULL)
                            RETURNING id;
                        """, (prod02_id, user_full_name, user_full_name))
                        header_03_id = cursor.fetchone()[0]

                    # Insert breakdown details into normalized columns
                    for deduction in source_deductions:
                        prod_info = deduction.get("product_info", "")  # e.g. "BA0188E (Lot: 0198A | Bag: 33)"
                        deduction_qty = deduction.get("deduction_qty", 0.0)
                        row_status = deduction.get("status", "Passed")

                        # --- PARSE STRING INTO COLUMNS ---
                        # Pattern matches: ProductCode (Lot: LotNum | Bag: BagNum)
                        parsed_code = prod_info.split(" (Lot:")[0].strip() if " (Lot:" in prod_info else prod_info

                        lot_num = ""
                        bag_num = None

                        match_lot = re.search(r"Lot:\s*([^\|]+)", prod_info)
                        if match_lot:
                            lot_num = match_lot.group(1).strip()

                        match_bag = re.search(r"Bag:\s*([^)]+)", prod_info)
                        if match_bag:
                            bag_str = match_bag.group(1).strip()
                            if bag_str.isdigit():
                                bag_num = int(bag_str)

                        # Insert into normalized columns
                        cursor.execute("""
                            INSERT INTO tbl_production03_detail (
                                production03_header_id, prod_code, lot_no, container_no, total_weight, status
                            ) VALUES (%s, %s, %s, %s, %s, %s);
                        """, (header_03_id, parsed_code, lot_num, bag_num, deduction_qty, row_status))

        conn.commit()
        return True, "Success"
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()


def confirm_production_record_in_db(prod_id):
    """
    Updates the confirmation_encoded_on timestamp for a given production ID.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE tbl_production_encode 
            SET confirmation_encoded_on = CURRENT_TIMESTAMP 
            WHERE prod_id = %s
        """, (prod_id,))

        conn.commit()
        return True, "Success"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()