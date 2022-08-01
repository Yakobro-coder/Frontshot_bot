import sqlalchemy
import os
from dotenv import load_dotenv
load_dotenv()


def connect():
    db = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@psql:5432/postgres"
    engine = sqlalchemy.create_engine(db)
    connection = engine.connect()

    return connection
