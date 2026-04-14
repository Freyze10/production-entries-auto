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
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_role_department ON tbl_role(department);")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_user(
            user_id SERIAL PRIMARY KEY,
            role_id INT NOT NULL,
            hostname VARCHAR(36) NOT NULL,
            password VARCHAR(36) NOT NULL, 
            FOREIGN KEY (role_id) REFERENCES tbl_role(role_id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_role_id ON tbl_user(role_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_hostname ON tbl_user(hostname);")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_formula01(
            form_id SERIAL PRIMARY KEY,
            index_no VARCHAR(22),
            date DATE,
            customer VARCHAR(62),
            prod_code VARCHAR(22) NOT NULL,
            prod_color VARCHAR(62),
            dosage DECIMAL(12,6),
            total_concentration DECIMAL(12,6),
            ld DECIMAL(12,6),
            mix_time VARCHAR(22),
            resin VARCHAR(36),
            application VARCHAR(36),
            colormatch_no VARCHAR(8),
            colormatch_date date,
            notes VARCHAR(256),
            date_time VARCHAR(32),
            is_deleted VARCHAR(5) DEFAULT 'False',
            is_used VARCHAR(5) DEFAULT 'False'
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_formula01_prod_code ON tbl_formula01(prod_code);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_formula01_customer ON tbl_formula01(customer);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_formula01_date ON tbl_formula01(date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_formula01_colormatch_no ON tbl_formula01(colormatch_no);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_formula01_is_deleted ON tbl_formula01(is_deleted);")

    cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_formula01_active 
            ON tbl_formula01(prod_code, customer, date) 
            WHERE is_deleted = 'False';
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

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_formula_encode_form_id ON tbl_formula_encode(form_id);")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_formula02(
            id SERIAL PRIMARY KEY,
            form_id INT,
            sequence_no INT,
            material_code VARCHAR(32),
            concentration DECIMAL(12,6),
            is_deleted VARCHAR(6) DEFAULT 'False',
            FOREIGN KEY (form_id) REFERENCES tbl_formula01(form_id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_formula02_form_id ON tbl_formula02(form_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_formula02_material_code ON tbl_formula02(material_code);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_formula02_form_seq ON tbl_formula02(form_id, sequence_no);")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_production01(
            prod_id SERIAL PRIMARY KEY,
            prod_date DATE,
            customer VARCHAR(62),
            form_id INT,
            index_no VARCHAR(32),
            prod_code VARCHAR(12),
            prod_color VARCHAR(62),
            dosage DECIMAL(12,6),
            ld DECIMAL(12,6),
            lot_no VARCHAR(128),
            order_no VARCHAR(36),
            colormatch_no VARCHAR(8),
            colormatch_date date,
            mix_time VARCHAR(32),
            machine_no VARCHAR(32),
            note VARCHAR(128),
            user_id VARCHAR(62),
            is_deleted VARCHAR(5) DEFAULT 'False',
            is_printed VARCHAR(5) DEFAULT 'False',
            inventory_c_date DATE,
            form_type VARCHAR(16)   
            )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_production01_prod_date ON tbl_production01(prod_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_production01_customer ON tbl_production01(customer);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_production01_prod_code ON tbl_production01(prod_code);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_production01_form_id ON tbl_production01(form_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_production01_lot_no ON tbl_production01(lot_no);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_production01_order_no ON tbl_production01(order_no);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_production01_is_deleted ON tbl_production01(is_deleted);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_production01_is_printed ON tbl_production01(is_printed);")

    cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_production01_date_customer 
            ON tbl_production01(prod_date, customer) 
            WHERE is_deleted = 'False';
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

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prod_encode_prod_id ON tbl_production_encode(prod_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prod_encode_encoded_on ON tbl_production_encode(encoded_on);")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_production_quantity(
            quantity_id SERIAL PRIMARY KEY,
            prod_id INT,
            quantity_req DECIMAL(12,6),
            quantity_batch DECIMAL(12,6),
            quantity_prod DECIMAL(12,6),
            FOREIGN KEY (prod_id) REFERENCES tbl_production01(prod_id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prod_quantity_prod_id ON tbl_production_quantity(prod_id);")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_production02(
            id SERIAL PRIMARY KEY,
            prod_id INT,
            sequence_no INT,
            material_code VARCHAR(32),
            large_scale DECIMAL(12,6),
            small_scale DECIMAL(12,6),
            total_weight DECIMAL(12,6),
            is_deleted VARCHAR(5) DEFAULT 'False',
            total_loss DECIMAL(12,6),
            total_consumption DECIMAL(12,6),
            FOREIGN KEY (prod_id) REFERENCES tbl_production01(prod_id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_production02_prod_id ON tbl_production02(prod_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_production02_material_code ON tbl_production02(material_code);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_production02_prod_seq ON tbl_production02(prod_id, sequence_no);")

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
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON tbl_audit_trail(timestamp DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_user_id ON tbl_audit_trail(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_action_type ON tbl_audit_trail(action_type);")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_raw_material_list(
            id SERIAL PRIMARY KEY,
            rm_code VARCHAR(50)
        )
    """)
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_rm_code_unique ON tbl_raw_material_list(rm_code);")

    # ==================== ADDITIONAL USEFUL INDEXES ====================
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prod_id ON tbl_production01(prod_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_qty_prod_id ON tbl_production_quantity(prod_id);")
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_production01_active_id_covering 
        ON tbl_production01 (is_deleted, prod_id)
        INCLUDE (prod_date, customer, prod_code, prod_color, lot_no)
        WHERE is_deleted = 'False';
    """)



    con.commit()
    cursor.close()
    con.close()










