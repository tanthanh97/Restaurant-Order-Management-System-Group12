import sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parents[1] / 'restaurant.db'

class Database:
    def __init__(self, path=DEFAULT_DB):
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('PRAGMA foreign_keys = ON')
        self.initialize()

    def initialize(self):
        self.conn.executescript('''
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS dining_tables(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, status TEXT NOT NULL DEFAULT 'Available');
        CREATE TABLE IF NOT EXISTS menu_items(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, category TEXT NOT NULL, price INTEGER NOT NULL CHECK(price>=0), available INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, table_id INTEGER NOT NULL REFERENCES dining_tables(id), status TEXT NOT NULL DEFAULT 'Active', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, discount INTEGER NOT NULL DEFAULT 0, payment_method TEXT, paid_at TEXT);
        CREATE TABLE IF NOT EXISTS order_details(id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(id), item_id INTEGER NOT NULL REFERENCES menu_items(id), quantity INTEGER NOT NULL CHECK(quantity>0), unit_price INTEGER NOT NULL, note TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'Pending');
        CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY, event TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        ''')
        if not self.conn.execute('SELECT 1 FROM dining_tables LIMIT 1').fetchone():
            self.conn.executemany('INSERT INTO dining_tables(name) VALUES(?)', [(f'T{i:02}',) for i in range(1, 21)])
        if not self.conn.execute('SELECT 1 FROM menu_items LIMIT 1').fetchone():
            self.conn.executemany('INSERT INTO menu_items(name,category,price) VALUES(?,?,?)', [
                ('Grilled Beef Steak','Main Dish',250000),('Spaghetti Bolognese','Main Dish',120000),('Fried Chicken','Main Dish',80000),
                ('Caesar Salad','Appetizer',70000),('Iced Latte','Drink',45000),('Tiramisu','Dessert',60000),('Orange Juice','Drink',35000)])
        self.conn.commit()

    def all(self, sql, args=()):
        return self.conn.execute(sql, args).fetchall()

    def one(self, sql, args=()):
        return self.conn.execute(sql, args).fetchone()

    def close(self):
        self.conn.close()
