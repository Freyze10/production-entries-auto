from db.connection import get_connection

def create_table():
    con = get_connection()
    cursor = con.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_role(
            role_id SERIAL PRIMARY KEY,
            department VARCHAR(36) NOT NULL,
            role VARCHAR(10) NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_user(
            user_id SERIAL PRIMARY KEY,
            role_id INT NOT NULL,
            hostname VARCHAR(36) NOT NULL,
            password VARCHAR(36) NOT NULL, 
            FOREIGN KEY (role_id) REFERENCES tbl_role(role_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_formula01(
            form_id SERIAL PRIMARY KEY,
            index_no VARCHAR(10),
            date DATE,
            customer VARCHAR(62),
            prod_code VARCHAR(12) NOT NULL,
            prod_color VARCHAR(62),
            dosage DECIMAL(6,2) NOT NULL,
            total_concentration DECIMAL(6,2),
            ld DECIMAL(6,2),
            mix_time VARCHAR(10),
            resin VARCHAR(36),
            application VARCHAR(36),
            colormatch_no VARCHAR(8),
            colormatch_date date,
            notes VARCHAR(128),
            date_time VARCHAR(32),
            is_deleted VARCHAR(5) DEFAULT 'False',
            is_used VARCHAR(5) DEFAULT 'False'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_formula_encode(
            encode_id SERIAL PRIMARY KEY,
            form_id INT,
            match_by VARCHAR(128),
            encoded_by VARCHAR(128),
            updated_by VARCHAR(128),
            FOREIGN KEY (form_id) REFERENCES tbl_formula01(form_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_formula02(
            id SERIAL PRIMARY KEY,
            form_id INT,
            sequence_no INT,
            material_code VARCHAR(32),
            concentration DECIMAL(6,6),
            is_deleted VARCHAR(6) DEFAULT 'False',
            FOREIGN KEY (form_id) REFERENCES tbl_formula01(form_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_production01(
            prod_id SERIAL PRIMARY KEY,
            prod_date DATE,
            customer VARCHAR(62),
            form_id INT,
            index_no VARCHAR(32),
            prod_code VARCHAR(12) NOT NULL,
            prod_color VARCHAR(62),
            dosage DECIMAL(6,2) NOT NULL,
            ld DECIMAL(6,2) NOT NULL,
            lot_no VARCHAR(128),
            order_no INT,
            colormatch_no VARCHAR(8),
            colormatch_date date NOT NULL,
            mix_time VARCHAR(32),
            machine_no VARCHAR(32),
            note VARCHAR(128),
            user_id INT,
            is_deleted VARCHAR(5) DEFAULT 'False',
            is_printed VARCHAR(5) DEFAULT 'False',
            inventory_c_date DATE,
            form_type VARCHAR(16),
            FOREIGN KEY (form_id) REFERENCES tbl_formula01(form_id),
            FOREIGN KEY (user_id) REFERENCES tbl_user(user_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_production_encode(
            encode_id SERIAL PRIMARY KEY,
            prod_id INT,
            prepared_by VARCHAR(128),
            encoded_by VARCHAR(128),
            encoded_on TIMESTAMP,
            confirmation_encoded_on TIMESTAMP,
            FOREIGN KEY (prod_id) REFERENCES tbl_production01(prod_id)
            )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_production_quantity(
            quantity_id SERIAL PRIMARY KEY,
            prod_id INT,
            quantity_req DECIMAL(10,6),
            quantity_batch DECIMAL(10,6),
            quantity_prod DECIMAL(10,6),
            FOREIGN KEY (prod_id) REFERENCES tbl_production01(prod_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_production02(
            id SERIAL PRIMARY KEY,
            prod_id INT,
            sequence_no INT,
            material_code VARCHAR(32),
            prod_a DECIMAL(6,6),
            prod_b DECIMAL(6,6),
            lab_a DECIMAL(6,6),
            lab_b DECIMAL(6,6),
            total_weight DECIMAL(6,6),
            is_deleted VARCHAR(5) DEFAULT 'False',
            loss DECIMAL(6,6),
            cons DECIMAL(6,6),
            FOREIGN KEY (prod_id) REFERENCES tbl_production01(prod_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_audit_trail(
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP,
            user_id INT,
            action_type VARCHAR(32),
            details VARCHAR(62),
            hostname VARCHAR(32),
            ip_adress VARCHAR(32),
            mac_adress VARCHAR(32),
            FOREIGN KEY (user_id) REFERENCES tbl_user(user_id)
        )
    """)

    con.commit()
    cursor.close()
    con.close()










