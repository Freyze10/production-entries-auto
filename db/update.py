from db.connection import get_connection


def cancel_production(prod_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
                UPDATE tbl_production01 SET is_deleted = "True" WHERE prod_id = %s
            """, (prod_id,))
        conn.commit()
        cursor.close()
        conn.close()

        # Placeholder for demonstration
        print(f"Database: Production {prod_id} marked as cancelled.")
        return True, "Success"

    except Exception as e:
        return False, str(e)