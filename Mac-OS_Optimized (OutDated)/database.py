import sqlite3
from contextlib import closing

DB_NAME = "fragrances.db"

# ---------------- CONNECTION ----------------
def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ---------------- SETUP ----------------
def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        # Fragrances
        c.execute("""
            CREATE TABLE IF NOT EXISTS fragrances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                description TEXT,
                gender TEXT,
                category TEXT,
                unit_cost REAL,
                sale_price REAL,
                inspired_by TEXT,
                quantity INTEGER,
                image TEXT
            )
        """)
        # Customers
        c.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT,
                phone TEXT,
                city TEXT,
                reference TEXT
            )
        """)
        # Sales
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
                FOREIGN KEY(fragrance_id) REFERENCES fragrances(id) ON DELETE CASCADE,
                FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE CASCADE
            )
        """)
        # Supplies
        c.execute("""
            CREATE TABLE IF NOT EXISTS supplies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                price REAL,
                purchase_link TEXT,
                quantity INTEGER
            )
        """)
        # Oils
        c.execute("""
            CREATE TABLE IF NOT EXISTS oils (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                size REAL,
                price REAL,
                purchase_link TEXT,
                quantity INTEGER
            )
        """)
        conn.commit()

# ---------------- FRAGRANCES ----------------
def insert_fragrance(data):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO fragrances 
            (name, description, gender, category, unit_cost, sale_price, inspired_by, quantity, image)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()

def get_all_fragrances_by_gender(gender):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM fragrances WHERE gender=?", (gender,))
        return c.fetchall()

def get_fragrance_by_id(fid):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM fragrances WHERE id=?", (fid,))
        return c.fetchone()

def get_fragrance_by_name(name):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM fragrances WHERE name=?", (name,))
        return c.fetchone()

def update_fragrance(fid, data):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE fragrances
            SET name=?, description=?, gender=?, category=?, unit_cost=?, sale_price=?, inspired_by=?, quantity=?, image=?
            WHERE id=?
        """, (*data, fid))
        conn.commit()

def delete_fragrance(fid):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM fragrances WHERE id=?", (fid,))
        conn.commit()

def update_fragrance_quantity(fid, quantity):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("UPDATE fragrances SET quantity=? WHERE id=?", (quantity, fid))
        conn.commit()

# ---------------- CUSTOMERS ----------------
def insert_customer(data):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO customers (name,email,phone,city,reference) VALUES (?, ?, ?, ?, ?)", data)
        conn.commit()

def get_all_customers():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM customers")
        return c.fetchall()

def get_customer_by_id(cid):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM customers WHERE id=?", (cid,))
        return c.fetchone()

def update_customer(cid, data):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE customers
            SET name=?, email=?, phone=?, city=?, reference=?
            WHERE id=?
        """, (*data, cid))
        conn.commit()

def delete_customer(cid):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM customers WHERE id=?", (cid,))
        conn.commit()

# ---------------- SALES ----------------
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
            LEFT JOIN fragrances f ON s.fragrance_id = f.id
            LEFT JOIN customers c ON s.customer_id = c.id
        """)
        return c.fetchall()

# ---------------- SUPPLIES ----------------
def insert_supply(data):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO supplies (name, price, purchase_link, quantity) VALUES (?, ?, ?, ?)", data)
        conn.commit()

def get_all_supplies():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM supplies")
        return c.fetchall()

def get_supply_by_id(sid):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM supplies WHERE id=?", (sid,))
        return c.fetchone()

def get_supply_by_name(name):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM supplies WHERE name=?", (name,))
        return c.fetchone()

def update_supply(sid, data):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE supplies
            SET name=?, price=?, purchase_link=?, quantity=?
            WHERE id=?
        """, (*data, sid))
        conn.commit()

def delete_supply(sid):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM supplies WHERE id=?", (sid,))
        conn.commit()

# ---------------- OILS ----------------
def insert_oil(data):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO oils (name, size, price, purchase_link, quantity) VALUES (?, ?, ?, ?, ?)", data)
        conn.commit()

def get_all_oils():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM oils")
        return c.fetchall()

def get_oil_by_id(oid):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM oils WHERE id=?", (oid,))
        return c.fetchone()

def get_oil_by_name(name):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM oils WHERE name=?", (name,))
        return c.fetchone()

def update_oil(oid, data):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE oils
            SET name=?, size=?, price=?, purchase_link=?, quantity=?
            WHERE id=?
        """, (*data, oid))
        conn.commit()

def delete_oil(oid):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM oils WHERE id=?", (oid,))
        conn.commit()

# ---------------- INITIALIZE ----------------
init_db()
