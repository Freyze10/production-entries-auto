from db.connection import get_connection


def print_production(prod_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
            UPDATE tbl_production01 SET is_printed = 'True' WHERE prod_id = %s
        """, (prod_id,))
    conn.commit()
    cursor.close()
    conn.close()


def cancel_production(prod_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
                UPDATE tbl_production01 SET is_deleted = 'True' WHERE prod_id = %s
            """, (prod_id,))
        conn.commit()
        cursor.close()
        conn.close()

        # Placeholder for demonstration
        print(f"Database: Production {prod_id} marked as cancelled.")
        return True, "Success"

    except Exception as e:
        return False, str(e)


def refresh_materialized():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("REFRESH MATERIALIZED VIEW mv_lot_parts;")
    conn.commit()
    cursor.close()
    conn.close()


def update_role_permissions(permission_list):
    # permission_list = [(role_id, access_id, state), ...]
    # Use: INSERT INTO tbl_role_permissions (role_id, access_id, is_enabled)
    # VALUES (%s, %s, %s)
    # ON CONFLICT (role_id, access_id) DO UPDATE SET is_enabled = EXCLUDED.is_enabled
    pass

