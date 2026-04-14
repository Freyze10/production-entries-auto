from db.connection import get_connection
from datetime import datetime


def create_current_user(workstation):
    con = get_connection()
    cursor = con.cursor()

    hostname = workstation['h']
    ip_address = workstation['i']
    mac_address = workstation['m']
    role_id = 2
    password = "mbpi"

    cursor.execute("""
        INSERT INTO tbl_user (role_id, hostname, ip_address, mac_address, password)
        VALUES (%s, %s, %s, %s, %s)
    """, (role_id, hostname, ip_address, mac_address, password))

    con.commit()
    cursor.close()
    con.close()


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