import psycopg2


def get_connection():
    # localhost
    return psycopg2.connect(
        host="localhost",
        dbname="db_production",
        user="postgres",
        password="password",
        port="5433"
    )

