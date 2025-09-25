import sqlite3
from contextlib import closing

DB_NAME = "fragrances.db"

def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ----------------- INIT -----------------
def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS fragrances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            description TEXT,
            gender TEXT,
            barcode TEXT,
            unit_cost REAL,
            sale_price REAL,
            inspired_by TEXT,
            quantity INTEGER,
            image_path TEXT
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            city TEXT,
            reference TEXT
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fragrance_id INTEGER,
            customer_id INTEGER,
            qty_sold INTEGER,
            unit_cost REAL,
            sale_price REAL,
            revenue REAL,
            profit REAL,
            date TEXT,
            FOREIGN KEY(fragrance_id) REFERENCES fragrances(id),
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )""")
        conn.commit()

# ----------------- FRAGRANCES -----------------
def insert_fragrance(data):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        INSERT INTO fragrances
        (name, description, gender, barcode, unit_cost, sale_price, inspired_by, quantity, image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()

def get_all_fragrances_by_gender(gender):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM fragrances WHERE gender=? ORDER BY name", (gender,))
        return c.fetchall()

def get_fragrance_by_id(f_id):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM fragrances WHERE id=?", (f_id,))
        return c.fetchone()

def get_fragrance_by_name(name):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM fragrances WHERE name=?", (name,))
        return c.fetchone()

def update_fragrance(f_id, data):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        UPDATE fragrances
        SET name=?, description=?, gender=?, barcode=?, unit_cost=?, sale_price=?, inspired_by=?, quantity=?, image_path=?
        WHERE id=?
        """, (*data, f_id))
        conn.commit()

def update_fragrance_quantity(f_id, qty):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("UPDATE fragrances SET quantity=? WHERE id=?", (qty, f_id))
        conn.commit()

def delete_fragrance(f_id):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM fragrances WHERE id=?", (f_id,))
        conn.commit()

# ----------------- CUSTOMERS -----------------
def insert_customer(data):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO customers (name,email,phone,city,reference) VALUES (?,?,?,?,?)", data)
        conn.commit()

def get_all_customers():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM customers ORDER BY name")
        return c.fetchall()

def get_customer_by_id(c_id):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM customers WHERE id=?", (c_id,))
        return c.fetchone()

def update_customer(c_id, data):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        UPDATE customers
        SET name=?, email=?, phone=?, city=?, reference=?
        WHERE id=?
        """, (*data, c_id))
        conn.commit()

def delete_customer(c_id):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM customers WHERE id=?", (c_id,))
        conn.commit()

# ----------------- SALES -----------------
def insert_sale(data):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        INSERT INTO sales
        (fragrance_id, customer_id, qty_sold, unit_cost, sale_price, revenue, profit, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()

def get_all_sales():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        SELECT s.id, f.name, c.name, s.qty_sold, s.unit_cost, s.sale_price, s.revenue, s.profit, s.date
        FROM sales s
        JOIN fragrances f ON s.fragrance_id = f.id
        JOIN customers c ON s.customer_id = c.id
        ORDER BY s.date DESC
        """)
        return c.fetchall()

# ----------------- INIT DB -----------------
init_db()
