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
                FOREIGN KEY (fragrance_id) REFERENCES fragrances(id) ON DELETE SET NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL
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
        # Expenses
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                amount REAL,
                date TEXT
            )
        """)
        conn.commit()

# ---------------- FRAGRANCE FUNCTIONS ----------------
def insert_fragrance(data):
    # data: (name, desc, gender, cat, u_cost, s_price, inspired, qty, img_path)
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO fragrances 
            (name, description, gender, category, unit_cost, sale_price, inspired_by, quantity, image) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()

def get_all_fragrances():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM fragrances")
        return c.fetchall()

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
    # data: (name, desc, gender, cat, u_cost, s_price, inspired, qty, img_path)
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
        # Deletes fragrance and cascade delete related sales via foreign key (ON DELETE SET NULL is used, so we need to delete sales manually or adjust FK constraint)
        # Assuming we keep FK as is (ON DELETE SET NULL for fragrance_id in sales table)
        c.execute("DELETE FROM fragrances WHERE id=?", (fid,))
        conn.commit()

def update_fragrance_quantity(fid, new_qty):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("UPDATE fragrances SET quantity=? WHERE id=?", (new_qty, fid))
        conn.commit()

# ---------------- CUSTOMER FUNCTIONS ----------------
def insert_customer(data):
    # data: (name, email, phone, city, reference)
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO customers (name, email, phone, city, reference) VALUES (?, ?, ?, ?, ?)", data)
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
    # data: (name, email, phone, city, reference)
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
        # Delete customer and cascade delete related sales
        c.execute("DELETE FROM customers WHERE id=?", (cid,))
        conn.commit()

# ---------------- SALES FUNCTIONS ----------------
def insert_sale(data):
    # data: (fragrance_id, customer_id, qty_sold, unit_cost, sale_price, revenue, profit, date)
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
            SELECT 
                s.id, f.name AS fragrance_name, c.name AS customer_name, 
                s.qty_sold, s.unit_cost, s.sale_price, s.revenue, s.profit, s.date
            FROM sales s
            LEFT JOIN fragrances f ON s.fragrance_id = f.id
            LEFT JOIN customers c ON s.customer_id = c.id
            ORDER BY s.date DESC
        """)
        return c.fetchall()

def get_sales_by_month(month, year):
    with get_conn() as conn:
        c = conn.cursor()
        # Use LIKE operator for YYYY-MM
        month_str = f"{year}-{month:02d}"
        c.execute("""
            SELECT 
                s.id, f.name AS fragrance_name, c.name AS customer_name, 
                s.qty_sold, s.unit_cost, s.sale_price, s.revenue, s.profit, s.date
            FROM sales s
            LEFT JOIN fragrances f ON s.fragrance_id = f.id
            LEFT JOIN customers c ON s.customer_id = c.id
            WHERE s.date LIKE ?
            ORDER BY s.date DESC
        """, (f"{month_str}%",))
        return c.fetchall()

# ---------------- SUPPLIES ----------------
def insert_supply(data):
    # data: (name, price, purchase_link, quantity)
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
    # data: (name, price, purchase_link, quantity)
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
    # data: (name, size, price, purchase_link, quantity)
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
    # data: (name, size, price, purchase_link, quantity)
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
        # CORRECTED: Removed stray backslash
        c.execute("DELETE FROM oils WHERE id=?", (oid,))
        conn.commit()

# ---------------- EXPENSES ----------------
def insert_expense(data):
    # data: (name, description, amount, date)
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO expenses (name, description, amount, date) VALUES (?, ?, ?, ?)", data)
        conn.commit()

def get_all_expenses():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM expenses ORDER BY date DESC")
        return c.fetchall()

def get_expense_by_id(eid):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM expenses WHERE id=?", (eid,))
        return c.fetchone()

# ---------------- NEW: REPORTING FUNCTIONS ----------------

def get_monthly_summary_data(month_year):
    """
    Fetches all sales and all expenses for a given month/year string (YYYY-MM).
    Returns a tuple: (sales_data, expense_data)
    """
    like_pattern = f"{month_year}%"
    with get_conn() as conn:
        c = conn.cursor()
        
        # 1. Sales Data
        # Returns: s.id, f.name, c.name, s.qty_sold, s.unit_cost, s.sale_price, s.revenue, s.profit, s.date
        sales_query = """
            SELECT 
                s.id, f.name AS fragrance_name, c.name AS customer_name, 
                s.qty_sold, s.unit_cost, s.sale_price, s.revenue, s.profit, s.date
            FROM sales s
            LEFT JOIN fragrances f ON s.fragrance_id = f.id
            LEFT JOIN customers c ON s.customer_id = c.id
            WHERE s.date LIKE ?
            ORDER BY s.date DESC
        """
        c.execute(sales_query, (like_pattern,))
        sales_data = c.fetchall()

        # 2. Expense Data
        # Returns: id, name, description, amount, date
        expense_query = "SELECT id, name, description, amount, date FROM expenses WHERE date LIKE ? ORDER BY date DESC"
        c.execute(expense_query, (like_pattern,))
        expense_data = c.fetchall()
        
    return sales_data, expense_data