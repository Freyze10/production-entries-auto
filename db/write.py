from db.connection import get_connection


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
