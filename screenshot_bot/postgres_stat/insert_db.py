from postgres_stat import db_connect
from sqlalchemy import exc


def insert_msg_info(user_id, msg_id, date_msg, url, connection=db_connect.connect()):
    try:
        connection.execute('INSERT INTO using_bot(user_id, msg_id, date_msg, url)'
                           'VALUES(%s, %s, %s, %s);', (user_id, msg_id, date_msg, url,))
    except exc.SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        print(error)
