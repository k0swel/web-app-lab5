import os

import pymysql
import pymysql.cursors
from flask import g
from werkzeug.security import generate_password_hash

DB_HOST     = os.environ.get('DB_HOST', 'localhost')
DB_PORT     = int(os.environ.get('DB_PORT', 3306))
DB_USER     = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_NAME     = os.environ.get('DB_NAME', 'lab5')


def get_db():
    if 'db' not in g:
        g.db = pymysql.connect(
            host=DB_HOST, port=DB_PORT,
            user=DB_USER, password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def query(sql, args=(), one=False):
    with get_db().cursor() as cur:
        cur.execute(sql, args)
        return cur.fetchone() if one else cur.fetchall()


def execute(sql, args=()):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(sql, args)
    db.commit()


def log_visit(user_id, path):
    execute(
        'INSERT INTO visit_logs (user_id, path) VALUES (%s, %s)',
        (user_id, path)
    )


def init_db():
    conn = pymysql.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS roles (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(64) NOT NULL UNIQUE
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    login VARCHAR(64) NOT NULL UNIQUE,
                    password_hash VARCHAR(256) NOT NULL,
                    first_name VARCHAR(64) NOT NULL,
                    last_name VARCHAR(64),
                    middle_name VARCHAR(64),
                    role_id INT,
                    FOREIGN KEY (role_id) REFERENCES roles(id)
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS visit_log (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    user_login VARCHAR(64),
                    visited_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    path VARCHAR(255) NOT NULL
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS visit_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    path VARCHAR(100) NOT NULL,
                    user_id INT,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                )
            ''')
            cur.execute(
                "INSERT IGNORE INTO roles (name) VALUES (%s), (%s)",
                ('Администратор', 'Пользователь')
            )
            cur.execute('SELECT COUNT(*) AS cnt FROM users')
            row = cur.fetchone()
            if row['cnt'] == 0:
                cur.execute('SELECT id FROM roles WHERE name = %s', ('Администратор',))
                role = cur.fetchone()
                cur.execute(
                    '''INSERT INTO users (login, password_hash, first_name, role_id)
                       VALUES (%s, %s, %s, %s)''',
                    ('admin', generate_password_hash('Admin1234'), 'Администратор', role['id'])
                )
        conn.commit()
    finally:
        conn.close()
