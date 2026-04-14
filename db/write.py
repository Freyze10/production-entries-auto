from db.connection import get_connection


def create_or_get_current_user(self):
    con = get_connection()
    cursor = con.cursor()

    hostname = self.workstation_info['h']
    ip_address = self.workstation_info['i']
    mac_address = self.workstation_info['m']
    role_id = 2
    password = "mbpi"

    cursor.execute("""
        INSERT INTO tbl_user (role_id, hostname, ip_address, mac_address, password)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (hostname) DO NOTHING;   -- Prevent duplicate hostname
    """, (role_id, hostname, ip_address, mac_address, password))

    con.commit()
    cursor.close()
    con.close()
