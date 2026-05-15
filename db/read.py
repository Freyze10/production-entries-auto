from datetime import datetime, timedelta
from functools import lru_cache

from psycopg2.extras import RealDictCursor
from db.connection import get_connection


def get_all_production_data():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            a.prod_id,
            TO_CHAR(a.prod_date, 'MM/DD/YYYY'),
            a.customer,
            a.prod_code,
            a.prod_color,
            a.lot_no,
            b.quantity_prod,
            a.index_no,
            a.is_printed  -- ADDED THIS
        FROM tbl_production01 a
        LEFT JOIN tbl_production_quantity b 
            ON a.prod_id = b.prod_id
        WHERE a.is_deleted = FALSE
        ORDER BY a.prod_id ASC;
    """)

    records = cur.fetchall()
    cur.close()
    conn.close()

    data = []
    for row in records:
        data.append([
            int(row[0]),                    # 0: prod_id
            str(row[1]) if row[1] else "",  # 1: date
            str(row[2]) if row[2] else "",  # 2: customer
            str(row[3]) if row[3] else "",  # 3: product_code
            str(row[4]) if row[4] else "",  # 4: product_color
            str(row[5]) if row[5] else "",  # 5: lot_no
            str(row[6]) if row[6] is not None else "0.0", # 6: qty
            str(row[7]) if row[7] else "",  # 7: index_no
            row[8]                          # 8: is_printed (BOOL)
        ])

    return data


@lru_cache(maxsize=1)
def get_cancelled_production_data():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            a.prod_id, 
            TO_CHAR(a.prod_date, 'MM/DD/YYYY'),
            a.customer, 
            a.prod_code, 
            a.prod_color, 
            a.lot_no, 
            b.quantity_prod,
            a.index_no,
            a.is_printed  -- ADD THIS LINE
        FROM tbl_production01 a
        LEFT JOIN tbl_production_quantity b 
            ON a.prod_id = b.prod_id
        WHERE a.is_deleted = TRUE  -- Check if this is BOOLEAN now
        ORDER BY a.prod_id ASC
    """)

    records = cur.fetchall()
    cur.close()
    conn.close()

    data = []
    for row in records:
        data.append([
            int(row[0]),                    # 0
            str(row[1]) if row[1] else "",  # 1
            str(row[2]) if row[2] else "",  # 2
            str(row[3]) if row[3] else "",  # 3
            str(row[4]) if row[4] else "",  # 4
            str(row[5]) if row[5] else "",  # 5
            str(row[6]) if row[6] is not None else "0.0", # 6
            str(row[7]) if row[7] else "",  # 7
            row[8]                          # 8: is_printed (CRITICAL FOR DELEGATE)
        ])

    return data

def get_single_production_details(prod_id):  # matrials details
    conn = get_connection()
    cur = conn.cursor()
    # , total_loss, total_consumption
    cur.execute("""
        SELECT prod_id, material_code, large_scale, small_scale, total_weight
        FROM tbl_production02
        WHERE prod_id = %s
        ORDER BY sequence_no ASC;
    """, (prod_id,))

    records = cur.fetchall()
    cur.close()
    conn.close()
    return records

def get_single_production_data(prod_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT *
        FROM tbl_production01 a
        LEFT JOIN tbl_production_encode e 
            ON a.prod_id = e.prod_id
        LEFT JOIN tbl_production_quantity q 
            ON a.prod_id = q.prod_id
        WHERE a.prod_id = %s
    """, (prod_id,))

    record = cur.fetchone()

    cur.close()
    conn.close()
    return record


def get_rm_code_lists():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""SELECT rm_code
                    FROM tbl_raw_material_list 
                    ORDER BY rm_code ASC""")
    records = cur.fetchall()

    cur.close()
    conn.close()
    if records:
        return [row[0] for row in records]
    else:
        return []


def check_mac_enabled(mac):
    """Returns True if the ID exists and is NOT deleted."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT EXISTS (
            SELECT 1 
            FROM tbl_user b
            JOIN tbl_mac_editor a ON b.user_id = a.user_id 
            WHERE b.mac_address = %s
        );""", (mac,))

        exists = cur.fetchone()[0]
        cur.close()
        conn.close()
        return exists
    except:
        return False


def check_production_exists(prod_id):
    """Returns True if the ID exists and is NOT deleted."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        # Updated to use native BOOLEAN FALSE
        cur.execute("SELECT EXISTS(SELECT 1 FROM tbl_production01 WHERE prod_id = %s AND is_deleted = FALSE)", (prod_id,))
        exists = cur.fetchone()[0]
        cur.close()
        conn.close()
        return exists
    except:
        return False


def get_latest_prod_id():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""SELECT COALESCE(MAX(prod_id), 0)
                    FROM tbl_production01""")
    record = cur.fetchone()

    cur.close()
    conn.close()
    return record[0]


def get_unprinted_reminders():
    """Fetches unprinted, non-deleted records from 60 to 30 days ago."""
    conn = get_connection()
    cur = conn.cursor()

    # Calculate date range
    today = datetime.now().date()
    end_date = today - timedelta(days=30)
    start_date = today - timedelta(days=60)

    query = """
        SELECT prod_id, customer, lot_no, prod_date 
        FROM public.tbl_production01 
        WHERE is_printed = false 
          AND is_deleted = false
          AND prod_date BETWEEN %s AND %s
        ORDER BY prod_date DESC
    """

    try:
        cur.execute(query, (start_date, end_date))
        records = cur.fetchall()
        return records
    finally:
        cur.close()
        conn.close()


def get_formula_select(product_code):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT index_no, form_id, customer, prod_code, prod_color, dosage, ld
        FROM tbl_formula01
        WHERE prod_code = %s 
        ORDER BY form_id DESC
    """, (product_code,))

    records = cur.fetchall()
    cur.close()
    conn.close()
    return records


def get_formula_materials(form_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT material_code, concentration FROM tbl_formula02 WHERE form_id = %s ORDER BY sequence_no ASC",
                (form_id,))
    records = cur.fetchall()

    cur.close()
    conn.close()
    return records


@lru_cache(maxsize=1)
def get_all_completer_data():
    conn = get_connection()
    cur = conn.cursor()

    # This single query gets distinct values for all 3 columns
    # and returns them as a single dictionary.
    cur.execute("""
        SELECT json_build_object(
            'customers', (SELECT array_agg(DISTINCT customer) FROM tbl_production01 WHERE customer IS NOT NULL),
            'prod_codes', (SELECT array_agg(DISTINCT prod_code) FROM tbl_production01 WHERE prod_code IS NOT NULL),
            'orders', (SELECT array_agg(DISTINCT order_no) FROM tbl_production01 WHERE order_no IS NOT NULL)
        )
    """)

    result = cur.fetchone()[0]  # fetches the dict

    cur.close()
    conn.close()
    return result


def get_lot_no():
    conn = get_connection()
    cur = conn.cursor()

    # Updated to use native BOOLEAN FALSE
    cur.execute("SELECT DISTINCT lot_no FROM tbl_production01 WHERE lot_no IS NOT NULL AND is_deleted = FALSE")

    lot_list = [row[0] for row in cur.fetchall()]

    cur.close()
    conn.close()
    return lot_list


def get_all_user_mac():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT mac_address FROM tbl_user")
    records = cur.fetchall()

    cur.close()
    conn.close()
    if records:
        return [row[0] for row in records]
    else:
        return []


def get_user_info_by_mac(mac):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT hostname, ip_address 
        FROM tbl_user 
        WHERE mac_address = %s
    """, (mac,))
    record = cur.fetchone()
    cur.close()
    conn.close()
    return record  # Returns (hostname, ip_address)


def get_audit_trail_report(start_date=None, end_date=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. Base Query - Added u.username to the selection
        query = """
            SELECT 
                a.timestamp, 
                u.hostname, 
                u.username, 
                a.action_type, 
                a.details, 
                u.ip_address, 
                u.mac_address
            FROM tbl_audit_trail a
            INNER JOIN tbl_user u ON a.user_id = u.user_id
        """

        params = []

        # 2. Add Date Filtering
        if start_date and end_date:
            query += " WHERE a.timestamp::date BETWEEN %s AND %s"
            params.extend([start_date, end_date])

        # 3. Add Ordering
        query += " ORDER BY a.timestamp DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        formatted_rows = []
        for row in rows:
            ts = row[0].strftime("%Y-%m-%d %I:%M %p") if row[0] else ""

            user_display = f"{row[1]}\\{row[2]}"

            formatted_rows.append([
                ts,  # Index 0: Timestamp
                user_display,  # Index 1: Hostname\Username
                row[3],  # Index 2: Action Type
                row[4],  # Index 3: Details
                row[5],  # Index 4: IP Address
                row[6]  # Index 5: MAC Address
            ])

        cursor.close()
        conn.close()
        return formatted_rows

    except Exception as e:
        print(f"Database Error: {e}")
        return []


def get_audit_date_bounds():
    """Returns (min_date, max_date) as Python date objects."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # Query for the absolute min and max timestamps
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM tbl_audit_trail")
        res = cursor.fetchone()
        cursor.close()
        conn.close()

        # Fallback to today's date if the table is empty
        min_date = res[0].date() if res[0] else datetime.now().date()
        max_date = res[1].date() if res[1] else datetime.now().date()

        return min_date, max_date
    except Exception as e:
        print(f"Error getting bounds: {e}")
        today = datetime.now().date()
        return today, today


def get_user_management_list():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
            SELECT u.user_id, u.hostname, u.username, u.ip_address, u.mac_address, r.role, r.department, u.password, u.role_id
            FROM tbl_user u
            JOIN tbl_role r ON u.role_id = r.role_id
            ORDER BY u.user_id ASC
        """)
    records = cur.fetchall()

    cur.close()
    conn.close()
    return records


def get_material_note(material_code):
    """
    Fetches the most recent note for a specific material code
    from the tbl_rm_incoming table.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT note 
        FROM public.tbl_rm_incoming 
        WHERE material_code = %s
        ORDER BY date DESC 
        LIMIT 1
    """, (material_code,))

    record = cur.fetchone()

    cur.close()
    conn.close()

    if record:
        return record[0]
    else:
        return None


def authenticate_user(username, password):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT r.role
            FROM tbl_user u
            JOIN tbl_role r ON u.role_id = r.role_id
            WHERE u.username = %s AND u.password = %s
            LIMIT 1
        """, (username, password))

        record = cur.fetchone()

        cur.close()
        conn.close()

        if record:
            return True, record[0]  # success, role
        else:
            return False, None

    except Exception as e:
        print(f"Auth Error: {e}")
        return False, None


def get_all_roles():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT role_id, role FROM tbl_role ORDER BY role_id ASC")
        records = cur.fetchall()
        cur.close()
        conn.close()
        return records
    except Exception as e:
        print(f"Error get_all_roles: {e}")
        return []


def get_access_points():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT access_id, access_name FROM tbl_access_points ORDER BY access_id ASC")
        records = cur.fetchall()
        cur.close()
        conn.close()
        return records
    except Exception as e:
        print(f"Error get_access_points: {e}")
        return []


def get_permission_matrix():
    try:
        conn = get_connection()
        cur = conn.cursor()
        # Fetches native BOOLEAN
        cur.execute("SELECT role_id, access_id, is_enabled FROM tbl_role_permissions")
        records = cur.fetchall()
        cur.close()
        conn.close()

        # Convert list to dictionary for high-speed lookup in Python
        # row[2] will be a Python True/False object
        return {(row[0], row[1]): row[2] for row in records}
    except Exception as e:
        print(f"Error get_permission_matrix: {e}")
        return {}


def get_allowed_access_points(role_name):
    """Returns a list of access_names that are enabled for this role."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        query = """
            SELECT a.access_name
            FROM tbl_role_permissions p
            JOIN tbl_role r ON p.role_id = r.role_id
            JOIN tbl_access_points a ON p.access_id = a.access_id
            WHERE r.role = %s AND p.is_enabled = TRUE
        """
        cur.execute(query, (role_name,))
        allowed = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return allowed
    except Exception as e:
        print(f"Error fetching permissions: {e}")
        return []