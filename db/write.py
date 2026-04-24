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