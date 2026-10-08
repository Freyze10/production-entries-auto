from db.connection import get_connection


def print_production(prod_id):
    conn = get_connection()
    cursor = conn.cursor()

    # Updated to use native BOOLEAN TRUE
    cursor.execute("""
            UPDATE tbl_production01 SET is_printed = TRUE WHERE prod_id = %s
        """, (prod_id,))
    conn.commit()
    cursor.close()
    conn.close()


def cancel_production(prod_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Updated to use native BOOLEAN TRUE
        cursor.execute("""
                UPDATE tbl_production01 SET is_deleted = TRUE WHERE prod_id = %s
            """, (prod_id,))
        conn.commit()
        cursor.close()
        conn.close()

        # Placeholder for demonstration
        print(f"Database: Production {prod_id} marked as cancelled.")
        return True, "Success"

    except Exception as e:
        return False, str(e)


def update_role_permissions(permission_list):
    """
    Saves the states of the checkboxes.
    permission_list: list of tuples -> [(role_id, access_id, state), ...]
    """
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Upsert: Insert if new, update is_enabled if already exists
        # This already handles Python True/False objects correctly for BOOLEAN columns
        query = """
            INSERT INTO tbl_role_permissions (role_id, access_id, is_enabled)
            VALUES (%s, %s, %s)
            ON CONFLICT (role_id, access_id) 
            DO UPDATE SET is_enabled = EXCLUDED.is_enabled;
        """

        cur.executemany(query, permission_list)
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error update_role_permissions: {e}")
        return False