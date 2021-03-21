import mysql.connector
from flask import g


def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(
                host='localhost',
                database='evaluation',
                user='username',
                password='password',
                use_pure=True,
                auth_plugin='mysql_native_password'
            )
    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)