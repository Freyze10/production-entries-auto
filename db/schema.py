from db.connection import get_connection


def create_table():
    con = get_connection()
    cursor = con.cursor()

    # 1. Roles
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_role(
            role_id SERIAL PRIMARY KEY,
            department VARCHAR(36) NOT NULL,
            role VARCHAR(10) NOT NULL,
            UNIQUE(department, role)
        )
    """)

    cursor.execute("""
        INSERT INTO tbl_role (department, role) VALUES 
            ('IT Department', 'ADMIN'),
            ('Production Department', 'Editor'),
            ('Laboratory Department', 'Viewer')
        ON CONFLICT (department, role) DO NOTHING; 
        CREATE INDEX IF NOT EXISTS idx_role_department ON tbl_role(department);
    """)

    # 2. Users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_user(
            user_id SERIAL PRIMARY KEY,
            role_id INT NOT NULL,
            hostname VARCHAR(36) NOT NULL,
            ip_address VARCHAR(32),
            mac_address VARCHAR(32) UNIQUE,
            username VARCHAR(50) NOT NULL,
            password VARCHAR(36) NOT NULL, 
            FOREIGN KEY (role_id) REFERENCES tbl_role(role_id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_role_id ON tbl_user(role_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_hostname ON tbl_user(hostname);")

    # 3. Formula Header (is_deleted and is_used converted to BOOLEAN)
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
            is_deleted BOOLEAN DEFAULT FALSE,
            is_used BOOLEAN DEFAULT FALSE
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_formula01_prod_code ON tbl_formula01(prod_code);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_formula01_is_deleted ON tbl_formula01(is_deleted);")

    # Updated Partial Index for Booleans
    cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_formula01_active 
            ON tbl_formula01(prod_code, customer, date) 
            WHERE is_deleted = FALSE;
    """)

    # 4. Formula Details (is_deleted converted to BOOLEAN)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_formula02(
            id SERIAL PRIMARY KEY,
            form_id INT,
            sequence_no INT,
            material_code VARCHAR(32),
            concentration DECIMAL(12,6),
            is_deleted BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (form_id) REFERENCES tbl_formula01(form_id)
        )
    """)

    # 5. Production Header (is_deleted and is_printed converted to BOOLEAN)
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
            is_deleted BOOLEAN DEFAULT FALSE,
            is_printed BOOLEAN DEFAULT FALSE,
            inventory_c_date DATE,
            form_type VARCHAR(16)   
            )
    """)
    # Updated Partial Index for Booleans
    cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_production01_date_customer 
            ON tbl_production01(prod_date, customer) 
            WHERE is_deleted = FALSE;
        """)

    # 6. Production Details (is_deleted converted to BOOLEAN)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_production02(
            id SERIAL PRIMARY KEY,
            prod_id INT,
            sequence_no INT,
            material_code VARCHAR(32),
            large_scale DECIMAL(12,6),
            small_scale DECIMAL(12,6),
            total_weight DECIMAL(12,6),
            is_deleted BOOLEAN DEFAULT FALSE,
            total_loss DECIMAL(12,6),
            total_consumption DECIMAL(12,6),
            FOREIGN KEY (prod_id) REFERENCES tbl_production01(prod_id)
        )
    """)

    # 7. Audit and Mapping tables (Keeping remaining as per your structure)
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
            quantity_req DECIMAL(12,6),
            quantity_batch DECIMAL(12,6),
            quantity_prod DECIMAL(12,6),
            FOREIGN KEY (prod_id) REFERENCES tbl_production01(prod_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_audit_trail(
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP,
            user_id INT,
            action_type VARCHAR(32),
            details VARCHAR(255),
            FOREIGN KEY (user_id) REFERENCES tbl_user(user_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_raw_material_list(
            id SERIAL PRIMARY KEY,
            rm_code VARCHAR(50) UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_rm_incoming (
            id SERIAL PRIMARY KEY,
            date DATE,
            material_code VARCHAR(50) NOT NULL UNIQUE,
            note TEXT
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_mac_editor (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL UNIQUE,
            FOREIGN KEY (user_id) REFERENCES tbl_user(user_id) ON DELETE CASCADE
        );
    """)

    # 8. Permissions (Already using BOOLEAN)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_access_points (
            access_id SERIAL PRIMARY KEY,
            access_name VARCHAR(50) UNIQUE 
        );

        CREATE TABLE IF NOT EXISTS tbl_role_permissions (
            role_id INT REFERENCES tbl_role(role_id) ON DELETE CASCADE,
            access_id INT REFERENCES tbl_access_points(access_id) ON DELETE CASCADE,
            is_enabled BOOLEAN DEFAULT FALSE,
            PRIMARY KEY (role_id, access_id)
        );
    """)

    # Data Initialization
    cursor.execute("""
            INSERT INTO tbl_access_points (access_name) VALUES 
                ('Production Records'), ('Manual Entry'), ('Auto Entry - MB'),
                ('Auto Entry - DC'), ('Audit Trail'), ('Permission Access')
            ON CONFLICT (access_name) DO NOTHING;
        """)

    cursor.execute("""
            INSERT INTO tbl_role_permissions (role_id, access_id, is_enabled)
            SELECT r.role_id, a.access_id, TRUE
            FROM tbl_role r, tbl_access_points a
            WHERE r.role = 'ADMIN'
            ON CONFLICT (role_id, access_id) DO NOTHING;
        """)

    # 9. Trigger logic
    cursor.execute("""
        CREATE OR REPLACE FUNCTION fn_sync_editor_list()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.role_id IN (1, 2) THEN
                INSERT INTO tbl_mac_editor (user_id)
                VALUES (NEW.user_id)
                ON CONFLICT (user_id) DO NOTHING;
            ELSE
                DELETE FROM tbl_mac_editor WHERE user_id = NEW.user_id;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    cursor.execute("DROP TRIGGER IF EXISTS trg_after_user_update ON tbl_user;")
    cursor.execute("""
        CREATE TRIGGER trg_after_user_update
        AFTER UPDATE ON tbl_user
        FOR EACH ROW
        WHEN (OLD.role_id IS DISTINCT FROM NEW.role_id)
        EXECUTE FUNCTION fn_sync_editor_list();
    """)

    con.commit()
    cursor.close()
    con.close()