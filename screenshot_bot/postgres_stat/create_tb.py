import sqlalchemy
import os
from dotenv import load_dotenv
load_dotenv()


def create_table(connection):
    connection.execute('create table if not exists using_bot('
                       'msg_id integer primary key,'
                       'user_id integer not null,'
                       'date_msg timestamptz not null,'
                       'url text not null'
                       ');')


if __name__ == '__main__':
    db = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@psql:5432/postgres"
    engine = sqlalchemy.create_engine(db)
    connection = engine.connect()

    create_table(connection)
