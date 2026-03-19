from connection import get_connection

def create_table():
    con = get_connection()
    cursor = con.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_role(
            role_id SERIAL PRIMARY KEY,
            department VARCHAR(36) NOT NULL,
            role VARCHAR(10) NOT NULL
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_user(
            user_id SERIAL PRIMARY KEY,
            role_id INT NOT NULL,
            hostname VARCHAR(36) NOT NULL,
            password VARCHAR(36) NOT NULL, 
            FOREIGN KEY (role_id) REFERENCES tbl_role(role_id)
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_customer(
            customer_id SERIAL PRIMARY KEY,
            customer_name VARCHAR(128)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_formula_encode(
            encode_id SERIAL PRIMARY KEY,
            match_by VARCHAR(128),
            encoded_by VARCHAR(128),
            updated_by VARCHAR(128)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_formula01(
            form_id SERIAL PRIMARY KEY,
            index_no VARCHAR(10),
            date DATE,
            customer_id INT NOT NULL,
            prod_code VARCHAR(12) NOT NULL,
            prod_color VARCHAR(32) NOT NULL,
        )
    """)


    con.commit()
    cursor.close()
    con.close()










