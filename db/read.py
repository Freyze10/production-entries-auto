from psycopg2.extras import RealDictCursor
from db.connection import get_connection


def get_all_production_data():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            a.prod_id, 
            a.prod_date, 
            a.customer, 
            a.prod_code, 
            a.prod_color, 
            a.lot_no, 
            b.quantity_prod 
        FROM tbl_production01 a
        LEFT JOIN tbl_production_quantity b 
            ON a.prod_id = b.prod_id
        ORDER BY a.prod_id ASC
    """)

    records = cur.fetchall()
    cur.close()
    conn.close()

    # Convert tuple rows to list of lists (exactly what you need for self.rows)
    data = []
    for row in records:
        data.append([
            str(row[0]),  # prod_id as string
            str(row[1]) if row[1] else "",  # production_date (handle None)
            str(row[2]) if row[2] else "",  # customer
            str(row[3]) if row[3] else "",  # product_code
            str(row[4]) if row[4] else "",  # product_color
            str(row[5]) if row[5] else "",  # lot_number
            str(row[6]) if row[6] is not None else "0.0"  # qty_produced
        ])

    return data


def get_single_production_details(prod_id):  # matrials details
    conn = get_connection()
    cur = conn.cursor()
    # , total_loss, total_consumption
    cur.execute("""
        SELECT prod_id, material_code, large_scale, small_scale, total_weight
        FROM tbl_production02
        WHERE material_code != '' AND prod_id = %s
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

def get_latest_prod_id():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""SELECT COALESCE(MAX(prod_id), 0)
                    FROM tbl_production01""")
    record = cur.fetchone()

    cur.close()
    conn.close()
    return record[0]


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


def get_all_completer_data():
    conn = get_connection()
    cur = conn.cursor()

    # This single query gets distinct values for all 4 columns
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
    return


def get_lot_no():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT lot_no 
        FROM tbl_production01 
        WHERE lot_no IS NOT NULL
        ORDER BY lot_no
    """)

    lot_list = [row[0] for row in cur.fetchall()]

    cur.close()
    conn.close()
    return lot_list




