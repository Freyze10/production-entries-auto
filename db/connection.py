import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

# Build paths inside the project like this: BASE_DIR / 'subdir'.
def load_environment():
    if getattr(sys, 'frozen', False):
        # Running as compiled .exe (PyInstaller)
        base_path = Path(sys.executable).parent
    else:
        # Running as normal Python script
        base_path = Path(__file__).resolve().parent.parent

    env_path = base_path / ".env"
    load_dotenv(env_path)

# Load the .env file
load_environment()

# dotENV
def get_connection():
    # localhost
    return psycopg2.connect(
        host=os.environ.get('DB_HOST'),
        dbname=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        port=os.environ.get('DB_PORT')
    )
def get_production_schema():
    return os.environ.get('PRODUCTION_SCHEMA')

def get_fg_schema():
    return os.environ.get('FG_SCHEMA')


def get_rm_endpoint():
    return os.environ.get('RM_ENDPOINT')

def get_rm_endpoint_key():
    return os.environ.get('RM_ENDPOINT_HEADERS')