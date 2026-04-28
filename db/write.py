from db.connection import get_connection
from datetime import datetime


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
    Saves or Updates a complete production record across 4 tables.
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

            # 3. Update Encode (Usually just confirmation date)
            cursor.execute("""
                UPDATE tbl_production_encode SET prepared_by=%s WHERE prod_id = %s
            """, (encode['prepared_by'], header['prod_id']))

            # 4. Refresh Materials (Delete old, Insert new is safest for sequences)
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

        # 5. Insert Materials (Common for both Insert/Update after cleanup)
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