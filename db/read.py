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
        ORDER BY a.prod_id DESC
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


def get_single_production_details(prod_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT material_code, large_scale, small_scale, total_weight, total_loss, total_consumption 
        FROM tbl_production02
        WHERE material_code != '' AND prod_id = %s
        ORDER BY seq ASC;
    """, (prod_id,))

    records = cur.fetchall()
    cur.close()
    conn.close()
    return records