import psycopg2


def get_connection():
    return psycopg2.connect(
        host="localhost",
        dbname="db_production",
        user="postgres",
        password="passsword",
        port="5433"
    )

def connect_db():
    connection = get_connection()
    return connection.cursor()
