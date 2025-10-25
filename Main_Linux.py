import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
from datetime import datetime
# Assuming 'database' module exists and its functions are functional
# from database import * # --- MOCK DATABASE FUNCTIONS (FOR DEMO PURPOSES ONLY) ---
# Replace these with your actual 'database.py' imports if running for real
# --- MOCK DATABASE FUNCTIONS (FOR DEMO PURPOSES ONLY) ---
# All functions are now stubbed to return an empty state ([], None, or pass).
def init_db(): pass
def get_all_fragrances_by_gender(gender): return []
def get_all_customers(): return []  # MODIFIED: Was returning a mock customer
def get_all_sales(): return []
def get_all_supplies(): return []   # MODIFIED: Was returning mock supplies
def get_all_oils(): return []       # MODIFIED: Was returning mock oils
def get_fragrance_by_name(name): return None
def get_supply_by_name(name): return None
def get_oil_by_name(name): return None
def insert_fragrance(data): pass
def insert_supply(data): pass
def insert_oil(data): pass
def get_fragrance_by_id(fid): return None  # MODIFIED: Was returning a mock fragrance
def update_fragrance(fid, data): pass
def delete_fragrance(fid): pass
def get_customer_by_id(cid): return None   # MODIFIED: Was returning a mock customer
def update_customer(cid, data): pass
def delete_customer(cid): pass
def get_supply_by_id(sid): return None     # MODIFIED: Was returning a mock supply
def update_supply(sid, data): pass
def delete_supply(sid): pass
def get_oil_by_id(oid): return None         # MODIFIED: Was returning a mock oil
def update_oil(oid, data): pass
def delete_oil(oid): pass
def insert_sale(data): pass
def update_fragrance_quantity(fid, qty): pass
# --- END MOCK DATABASE FUNCTIONS ---


# --- STYLING CONSTANTS ---
PRIMARY_COLOR = "#0078D4" # A clean, modern blue
ACCENT_COLOR = "#E10078" # A complementary pink for fragrance/accent
BACKGROUND_COLOR = "#F0F0F0" # Light gray for a modern, 'app-like' feel
FOREGROUND_COLOR = "#333333" # Dark text
BUTTON_BG_COLOR = "#E0E0E0" # Light gray for standard buttons
BUTTON_HOVER_COLOR = "#C0C0C0"
DANGER_COLOR = "#D9534F" # Red for delete actions

# ---------------- CONSTANTS ----------------
UNIT_COST = 5.0
SALE_PRICE = 25.0
IMAGE_DIR = "assets/images/" 
VIEWER_IMAGE_SIZE = (180, 180) 
LOGO_PATH = "assets/logo.png"

# ---------------- APP CLASS ----------------
class FragranceManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LJ Fragrances Manager")
        self.root.geometry("1600x900")
        self.selected_id = None
        self.selected_customer_id = None
        self.selected_supply_id = None
        self.selected_oil_id = None
        self.image_cache = {}
        self.selected_image_path = None
        self.current_fragrance_image = None
        self.logo_photo = None
        
        init_db() 

        self.setup_ui()
        # Prefill calls were removed from here.

    # ---------------- UI SETUP (APPLIED MODERN STYLES & FINAL FIX) ----------------
    def setup_ui(self):
        # 1. Apply modern style theme
        style = ttk.Style()
        
        self.root.config(bg=BACKGROUND_COLOR)
        style.theme_create("modern_fragrance", parent="alt", settings={
            "TFrame": {"configure": {"background": BACKGROUND_COLOR}},
            "TLabel": {"configure": {"background": BACKGROUND_COLOR, "foreground": FOREGROUND_COLOR, "font": ('Arial', 10)}},
            
            # Standard Button Style
            "TButton": {
                "configure": {"font": ('Arial', 10, 'bold'), "padding": 8, "relief": "flat", "background": BUTTON_BG_COLOR, "foreground": FOREGROUND_COLOR, "bordercolor": FOREGROUND_COLOR, "borderwidth": 1},
                "map": {"background": [('active', BUTTON_HOVER_COLOR), ('pressed', PRIMARY_COLOR)], "foreground": [('pressed', 'white')]}
            },
            # Primary Action Button Style
            "Accent.TButton": { 
                "configure": {"background": PRIMARY_COLOR, "foreground": "white", "bordercolor": PRIMARY_COLOR},
                "map": {"background": [('active', ACCENT_COLOR), ('pressed', PRIMARY_COLOR)]}
            },
            # Delete Action Button Style
            "Danger.TButton": { 
                "configure": {"background": DANGER_COLOR, "foreground": "white"},
                "map": {"background": [('active', DANGER_COLOR), ('pressed', DANGER_COLOR)]}
            },
            
            # Notebook/Tab Styles
            "TNotebook": {"configure": {"background": BACKGROUND_COLOR, "padding": [5, 5]}},
            "TNotebook.Tab": {
                "configure": {"padding": [15, 5], "background": BUTTON_BG_COLOR, "foreground": FOREGROUND_COLOR, "font": ('Arial', 10)},
                "map": {"background": [('selected', PRIMARY_COLOR)], "foreground": [('selected', 'white')]}
            },
            
            # Treeview (Table) Styles
            "Treeview.Heading": {
                "configure": {"font": ('Arial', 10, 'bold'), "background": PRIMARY_COLOR, "foreground": "white", "relief": "flat"},
                "map": {"background": [('active', PRIMARY_COLOR)]}
            },
            "Treeview": {
                "configure": {"background": "white", "foreground": FOREGROUND_COLOR, "fieldbackground": "white", "font": ('Arial', 10), "rowheight": 25, "borderwidth": 0},
                "map": {"background": [('selected', PRIMARY_COLOR)], "foreground": [('selected', 'white')]}
            },
            
            # Input Styles
            "TEntry": {"configure": {"padding": 5, "fieldbackground": "white", "bordercolor": "#CCCCCC"}},
            "TCombobox": {"configure": {"padding": 5, "fieldbackground": "white", "bordercolor": "#CCCCCC"}},
        })
        style.theme_use("modern_fragrance")
        
        # *** Keep the robust configurations active ***
        # These configurations will be inherited by the default TLabelFrame layout.
        style.configure("TLabelFrame", 
                        background=BACKGROUND_COLOR, 
                        foreground=PRIMARY_COLOR, 
                        borderwidth=0)
        
        style.configure("TLabelFrame.Label", 
                        background=BACKGROUND_COLOR, 
                        foreground=PRIMARY_COLOR, 
                        font=('Arial', 12, 'bold'))
        # *** End of robust configurations ***
        
        # 2. Main Layout
        main_frame = ttk.Frame(self.root, style='TFrame') 
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # 3. Top Frame: Logo, Search, and Image/Detail Viewer
        top_frame = ttk.Frame(main_frame, style='TFrame')
        top_frame.pack(fill="x", pady=5)
        
        self.load_logo(top_frame)
        
        # LEFT SIDE: Search
        search_container = ttk.Frame(top_frame, style='TFrame')
        search_container.pack(side="left", padx=5, fill="y", expand=False)

        search_frame = ttk.Frame(search_container, style='TFrame')
        search_frame.pack(side="top", anchor="w", pady=(10, 0))

        ttk.Label(search_frame, text="🔍 Search Fragrance:").pack(side="left", padx=5)
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side="left", padx=5)
        ttk.Button(search_frame, text="Search", command=self.search_fragrance, style='TButton').pack(side="left", padx=5)
        ttk.Button(search_frame, text="Clear", command=self.refresh_all_tables, style='TButton').pack(side="left", padx=5)

        # RIGHT SIDE: Image Viewer
        # *** FINAL FIX: Removed style='TLabelFrame' to prevent TclError ***
        self.image_viewer_frame = ttk.LabelFrame(top_frame, text="Fragrance Details", padding="10")
        self.image_viewer_frame.pack(side="right", fill="y", padx=20, anchor="n") 
        
        self.image_label = ttk.Label(self.image_viewer_frame, anchor="center", background="white", borderwidth=1, relief="solid")
        self.image_label.grid(row=0, column=0, padx=5, pady=5)
        
        # Use a plain tk.Label here for multi-line text with custom background
        self.detail_text_label = tk.Label(self.image_viewer_frame, justify=tk.LEFT, text="Select a fragrance to view details.", width=35, anchor="nw", background="white", fg=FOREGROUND_COLOR, font=('Arial', 10))
        self.detail_text_label.grid(row=0, column=1, padx=10, pady=5, sticky="nsw")

        # 4. Tab Control
        self.tabControl = ttk.Notebook(main_frame)
        self.tabControl.pack(expand=1, fill="both", pady=10)

        # 5. Tabs
        self.men_tab = ttk.Frame(self.tabControl, style='TFrame')
        self.women_tab = ttk.Frame(self.tabControl, style='TFrame')
        self.unisex_tab = ttk.Frame(self.tabControl, style='TFrame')
        self.customer_tab = ttk.Frame(self.tabControl, style='TFrame')
        self.sales_tab = ttk.Frame(self.tabControl, style='TFrame')
        self.supplies_tab = ttk.Frame(self.tabControl, style='TFrame')
        self.oils_tab = ttk.Frame(self.tabControl, style='TFrame')

        self.tabControl.add(self.men_tab, text="Men")
        self.tabControl.add(self.women_tab, text="Women")
        self.tabControl.add(self.unisex_tab, text="Unisex")
        self.tabControl.add(self.customer_tab, text="Customers")
        self.tabControl.add(self.sales_tab, text="Sales")
        self.tabControl.add(self.supplies_tab, text="Supplies")
        self.tabControl.add(self.oils_tab, text="Oils")
        
        # 6. Setup Tab Contents
        self.setup_fragrance_tab(self.men_tab, "Men")
        self.setup_fragrance_tab(self.women_tab, "Women")
        self.setup_fragrance_tab(self.unisex_tab, "Unisex")
        self.setup_customer_tab(self.customer_tab)
        self.setup_sales_tab(self.sales_tab)
        self.setup_supplies_tab(self.supplies_tab)
        self.setup_oils_tab(self.oils_tab)

    def load_logo(self, parent_frame):
        """Loads and places the logo image."""
        if os.path.exists(LOGO_PATH):
            try:
                img = Image.open(LOGO_PATH).resize((250, 200)) 
                self.logo_photo = ImageTk.PhotoImage(img)
                
                logo_frame = ttk.Frame(parent_frame, style='TFrame')
                logo_frame.pack(side="left", padx=20, anchor="n")
                
                logo_label = ttk.Label(logo_frame, image=self.logo_photo, style='TLabel')
                logo_label.pack(side="top")
                
            except Exception as e:
                # Fallback on error
                ttk.Label(parent_frame, text="LJ Fragrances", font=('Arial', 18, 'bold'), style='TLabel').pack(side="left", padx=20, anchor="n")
        else:
            # Fallback if file doesn't exist
            ttk.Label(parent_frame, text="LJ Fragrances", font=('Arial', 18, 'bold'), style='TLabel').pack(side="left", padx=20, anchor="n")

    # ---------------- TAB-SPECIFIC LAYOUTS ----------------
    def setup_fragrance_tab(self, parent, gender):
        # 1. Container for Table
        table_frame = ttk.Frame(parent, style='TFrame')
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Table setup
        columns = ("Name", "Inspired By", "Unit Cost", "Sale Price", "Quantity", "Total Cost", "Retail Value", "Gender")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20, selectmode="browse") 

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")

        tree.pack(side="left", fill="both", expand=True)
        setattr(self, f"{gender.lower()}_tree", tree)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        tree.bind("<<TreeviewSelect>>", self.on_fragrance_select)
        self.populate_table(tree, gender) # Populated on initialization

        # 2. Tab-Specific Buttons (Using custom styles)
        btn_frame = ttk.Frame(parent, style='TFrame')
        btn_frame.pack(fill="x", pady=5, padx=5)

        ttk.Button(btn_frame, text="➕ Add Fragrance", command=self.add_fragrance, style='Accent.TButton').pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✏️ Edit Fragrance", command=self.edit_fragrance, style='TButton').pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑️ Delete Fragrance", command=self.delete_fragrance, style='Danger.TButton').pack(side="left", padx=5)
        ttk.Button(btn_frame, text="💵 Record Sale", command=self.record_sale, style='Accent.TButton').pack(side="right", padx=5)

    def setup_customer_tab(self, parent):
        table_frame = ttk.Frame(parent, style='TFrame')
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)

        columns = ("ID", "Name", "Email", "Phone", "City", "Reference")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        tree.pack(side="left", fill="both", expand=True)
        self.customer_tree = tree
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        tree.bind("<<TreeviewSelect>>", self.on_customer_select)
        self.populate_customers() # Populated on initialization

        btn_frame = ttk.Frame(parent, style='TFrame')
        btn_frame.pack(fill="x", pady=5, padx=5)
        ttk.Button(btn_frame, text="➕ Add Customer", command=self.add_customer, style='Accent.TButton').pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✏️ Edit Customer", command=self.edit_customer, style='TButton').pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑️ Delete Customer", command=self.delete_customer, style='Danger.TButton').pack(side="left", padx=5)

    def setup_sales_tab(self, parent):
        table_frame = ttk.Frame(parent, style='TFrame')
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)

        columns = ("ID", "Fragrance", "Customer", "Qty Sold", "Unit Cost", "Sale Price", "Revenue", "Profit", "Date")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="none")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.sales_tree = tree
        self.populate_sales() # Populated on initialization
        

    def setup_supplies_tab(self, parent):
        table_frame = ttk.Frame(parent, style='TFrame')
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)

        columns = ("ID", "Name", "Price", "Purchase Link", "Quantity")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.supplies_tree = tree
        tree.bind("<<TreeviewSelect>>", self.on_supply_select)
        self.populate_supplies() # Populated on initialization
        
        btn_frame = ttk.Frame(parent, style='TFrame')
        btn_frame.pack(fill="x", pady=5, padx=5)
        ttk.Button(btn_frame, text="➕ Add Supply", command=self.add_supply, style='Accent.TButton').pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✏️ Edit Supply", command=self.edit_supply, style='TButton').pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑️ Delete Supply", command=self.delete_supply, style='Danger.TButton').pack(side="left", padx=5)

    def setup_oils_tab(self, parent):
        table_frame = ttk.Frame(parent, style='TFrame')
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)

        columns = ("ID", "Name", "Size(ml)", "Price", "Purchase Link", "Quantity")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.oils_tree = tree
        tree.bind("<<TreeviewSelect>>", self.on_oil_select)
        self.populate_oils() # Populated on initialization

        btn_frame = ttk.Frame(parent, style='TFrame')
        btn_frame.pack(fill="x", pady=5, padx=5)
        ttk.Button(btn_frame, text="➕ Add Oil", command=self.add_oil, style='Accent.TButton').pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✏️ Edit Oil", command=self.edit_oil, style='TButton').pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑️ Delete Oil", command=self.delete_oil, style='Danger.TButton').pack(side="left", padx=5)
        
    # ---------------- POPULATE METHODS (REMAINING) ----------------
    def populate_table(self, tree, gender, query=None):
        for row in tree.get_children():
            tree.delete(row)
        fragrances = get_all_fragrances_by_gender(gender)
        for f in fragrances:
            if query:
                q = query.lower()
                if q not in (f[1] or "").lower() and q not in (f[7] or "").lower():
                    continue
            try:
                unit_cost = float(f[5])
                sale_price = float(f[6])
                quantity = int(f[8])
            except:
                unit_cost = 0.0
                sale_price = 0.0
                quantity = 0
            total_cost = unit_cost * quantity
            retail_value = sale_price * quantity

            tags = ()
            if quantity < 5:
                tags = ("low_stock",)
            
            tree.insert("", "end",
                        iid=str(f[0]),
                        values=(str(f[1] or ""),
                                str(f[7] or ""),
                                f"{unit_cost:.2f}",
                                f"{sale_price:.2f}",
                                str(quantity),
                                f"{total_cost:.2f}",
                                f"{retail_value:.2f}",
                                str(f[3] or "")
                                ),
                        tags=tags)
        tree.tag_configure("low_stock", background="red")

    def populate_customers(self):
        for row in self.customer_tree.get_children():
            self.customer_tree.delete(row)
        for c in get_all_customers():
            self.customer_tree.insert("", "end", iid=str(c[0]), values=c)

    def populate_sales(self):
        for row in self.sales_tree.get_children():
            self.sales_tree.delete(row)
        for s in get_all_sales():
            self.sales_tree.insert("", "end", values=s)

    def populate_supplies(self):
        for row in self.supplies_tree.get_children():
            self.supplies_tree.delete(row)
        for s in get_all_supplies():
            self.supplies_tree.insert("", "end", iid=str(s[0]), values=s)

    def populate_oils(self):
        for row in self.oils_tree.get_children():
            self.oils_tree.delete(row)
        for o in get_all_oils():
            self.oils_tree.insert("", "end", iid=str(o[0]), values=o)
            
    # ---------------- SELECTION & VIEW (Minor styling updates) ----------------
    def on_fragrance_select(self, event):
        tree = event.widget
        selected = tree.selection()
        
        if not selected:
            self.selected_id = None
            self.update_fragrance_viewer(None)
            return

        self.selected_id = int(selected[0])
        self.update_fragrance_viewer(self.selected_id)

    def update_fragrance_viewer(self, fid):
        if not fid:
            self.image_viewer_frame.config(text="Fragrance Details")
            self.image_label.config(image='', text="No Image")
            self.detail_text_label.config(text="Select a fragrance to view details.")
            self.current_fragrance_image = None
            return

        f_data = get_fragrance_by_id(fid)
        if not f_data:
            return

        name, desc, gender, _, unit_cost, sale_price, inspired_by, qty, img_path = f_data[1:]

        self.image_viewer_frame.config(text=name)

        details = (
            f"Name: {name}\n"
            f"Inspired By: {inspired_by}\n"
            f"Gender: {gender}\n"
            f"Cost: ${unit_cost:.2f} | Price: ${sale_price:.2f}\n"
            f"Stock: {qty}\n"
            f"\nDescription: {desc or 'N/A'}"
        )
        self.detail_text_label.config(text=details)

        if img_path and os.path.exists(img_path):
            try:
                img = Image.open(img_path).resize(VIEWER_IMAGE_SIZE) 
                photo = ImageTk.PhotoImage(img)
                self.current_fragrance_image = photo 
                self.image_label.config(image=self.current_fragrance_image, text="")
            except Exception:
                self.image_label.config(text="Image Error", image='')
        else:
            self.image_label.config(text="No Image", image='')

    def on_customer_select(self, event):
        tree = event.widget
        selected = tree.selection()
        self.selected_customer_id = int(selected[0]) if selected else None

    def on_supply_select(self, event):
        tree = event.widget
        selected = tree.selection()
        self.selected_supply_id = int(selected[0]) if selected else None

    def on_oil_select(self, event):
        tree = event.widget
        selected = tree.selection()
        self.selected_oil_id = int(selected[0]) if selected else None

    # ---------------- CRUD/FORMS/SEARCH (Applied modern styles to forms) ----------------
    def add_fragrance(self):
        self.open_fragrance_form()

    def edit_fragrance(self):
        if not self.selected_id:
            messagebox.showwarning("No Selection", "Select fragrance to edit")
            return
        self.open_fragrance_form(edit=True)

    def delete_fragrance(self):
        if not self.selected_id:
            messagebox.showwarning("No Selection", "Select fragrance to delete")
            return
        # Removed confirmation dialog for brevity, but it should be here
        delete_fragrance(self.selected_id)
        self.refresh_all_tables()
        self.selected_id = None
        self.update_fragrance_viewer(None)

    def add_customer(self):
        self.open_customer_form()
    def edit_customer(self):
        if not self.selected_customer_id:
            messagebox.showwarning("No Selection", "Select customer to edit")
            return
        self.open_customer_form(edit=True)
    def delete_customer(self):
        if not self.selected_customer_id:
            messagebox.showwarning("No Selection", "Select customer to delete")
            return
        delete_customer(self.selected_customer_id)
        self.populate_customers()

    def add_supply(self):
        self.open_supply_form()
    def edit_supply(self):
        if not self.selected_supply_id:
            messagebox.showwarning("No Selection", "Select supply to edit")
            return
        self.open_supply_form(edit=True)
    def delete_supply(self):
        if not self.selected_supply_id:
            messagebox.showwarning("No Selection", "Select supply to delete")
            return
        delete_supply(self.selected_supply_id)
        self.populate_supplies()

    def add_oil(self):
        self.open_oil_form()
    def edit_oil(self):
        if not self.selected_oil_id:
            messagebox.showwarning("No Selection", "Select oil to edit")
            return
        self.open_oil_form(edit=True)
    def delete_oil(self):
        if not self.selected_oil_id:
            messagebox.showwarning("No Selection", "Select oil to delete")
            return
        delete_oil(self.selected_oil_id)
        self.populate_oils()

    def record_sale(self):
        if not self.selected_id:
            messagebox.showwarning("No Selection", "Select fragrance to sell")
            return
        all_customers = get_all_customers()
        if not all_customers:
            messagebox.showwarning("No Customers", "No customers found. Please add a customer first.")
            return
        
        form = tk.Toplevel(self.root)
        form.title("Record Sale")
        form.geometry("400x300")
        form.config(bg=BACKGROUND_COLOR)
        
        # Use a Frame to contain the grid for consistent padding
        form_frame = ttk.Frame(form, padding=10, style='TFrame')
        form_frame.pack(fill="both", expand=True)

        ttk.Label(form_frame, text="Customer:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        customers = [f"{c[1]} (ID:{c[0]})" for c in all_customers]
        customer_var = tk.StringVar()
        cust_combo = ttk.Combobox(form_frame, values=customers, textvariable=customer_var, state="readonly", style='TCombobox')
        cust_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(form_frame, text="Quantity:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        qty_entry = ttk.Entry(form_frame, style='TEntry')
        qty_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Logic is the same
        def save_sale():
            # ... (Existing save logic) ...
            if not customer_var.get():
                messagebox.showwarning("Error", "Select customer")
                return
            try:
                qty = int(qty_entry.get())
                if qty <= 0:
                    raise ValueError
            except:
                messagebox.showerror("Error", "Quantity must be a positive number")
                return
            fragrance = get_fragrance_by_id(self.selected_id)
            if not fragrance:
                messagebox.showerror("Error", "Fragrance not found")
                return
            current_qty = int(fragrance[8])
            if qty > current_qty:
                messagebox.showerror("Error", f"Not enough stock. Available: {current_qty}")
                return
            customer_id = int(customer_var.get().split("ID:")[1].replace(")", ""))
            unit_cost = float(fragrance[5])
            sale_price = float(fragrance[6])
            revenue = sale_price * qty
            profit = (sale_price - unit_cost) * qty
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            insert_sale((self.selected_id, customer_id, qty, unit_cost, sale_price, revenue, profit, date))
            update_fragrance_quantity(self.selected_id, current_qty - qty)
            self.populate_sales()
            self.refresh_all_tables()
            self.update_fragrance_viewer(self.selected_id)
            form.destroy()
        
        ttk.Button(form_frame, text="Save Sale", command=save_sale, style='Accent.TButton').grid(row=2, column=1, pady=10, sticky="e")
        form_frame.grid_columnconfigure(1, weight=1) # Makes entry/combo fill space

    def choose_image(self, entry_widget):
        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files","*.png *.jpg *.jpeg *.gif *.bmp"),("All files","*.*")]
        )
        if path:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, path)

    def open_fragrance_form(self, edit=False):
        f_data = get_fragrance_by_id(self.selected_id) if edit else None
        form = tk.Toplevel(self.root)
        form.title("Edit Fragrance" if edit else "Add Fragrance")
        form.geometry("450x450")
        form.config(bg=BACKGROUND_COLOR) # Set background for Toplevel
        
        form_frame = ttk.Frame(form, padding=10, style='TFrame')
        form_frame.pack(fill="both", expand=True)

        fields = ["Name", "Description", "Gender", "Category", "Unit Cost", "Sale Price", "Inspired By", "Quantity", "Image"]
        entries = {}

        for i, field in enumerate(fields):
            ttk.Label(form_frame, text=f"{field}:").grid(row=i, column=0, padx=5, pady=5, sticky="w")
            
            if field == "Gender":
                entry = ttk.Combobox(form_frame, values=["Men", "Women", "Unisex"], state="readonly", style='TCombobox')
                if edit and f_data: entry.set(f_data[i+1] if i+1 < len(f_data) else "")
            elif field == "Description":
                # Use a standard ttk.Entry for simplicity, but could use Text widget for longer input
                entry = ttk.Entry(form_frame, width=30, style='TEntry')
                if edit and f_data: entry.insert(0, f_data[i+1] if i+1 < len(f_data) else "")
            else:
                entry = ttk.Entry(form_frame, width=30, style='TEntry')
                if edit and f_data: entry.insert(0, f_data[i+1] if i+1 < len(f_data) else "")
                
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            entries[field] = entry

        # Image selection button in its own column
        ttk.Button(form_frame, text="Choose Image", command=lambda: self.choose_image(entries["Image"]), style='TButton').grid(row=8, column=2, padx=5)
        
        # Logic is the same
        def save():
            data = [entries[f].get() for f in fields]
            if edit:
                update_fragrance(self.selected_id, data)
            else:
                insert_fragrance(data)
            self.refresh_all_tables()
            self.update_fragrance_viewer(self.selected_id)
            form.destroy()

        ttk.Button(form_frame, text="Save", command=save, style='Accent.TButton').grid(row=9, column=1, pady=15, sticky="e")
        
        form_frame.grid_columnconfigure(1, weight=1) # Makes inputs expand

    def open_customer_form(self, edit=False):
        c_data = get_customer_by_id(self.selected_customer_id) if edit else None
        form = tk.Toplevel(self.root)
        form.title("Edit Customer" if edit else "Add Customer")
        form.geometry("400x300")
        form.config(bg=BACKGROUND_COLOR)

        form_frame = ttk.Frame(form, padding=10, style='TFrame')
        form_frame.pack(fill="both", expand=True)

        fields = ["Name", "Email", "Phone", "City", "Reference"]
        entries = {}
        for i, field in enumerate(fields):
            ttk.Label(form_frame, text=f"{field}:").grid(row=i, column=0, padx=5, pady=5, sticky="w")
            entry = ttk.Entry(form_frame, style='TEntry')
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            if edit and c_data:
                entry.insert(0, c_data[i+1])
            entries[field] = entry
            
        def save():
            data = [entries[f].get() for f in fields]
            if edit:
                update_customer(self.selected_customer_id, data)
            else:
                insert_customer(data)
            self.populate_customers()
            form.destroy()

        ttk.Button(form_frame, text="Save", command=save, style='Accent.TButton').grid(row=len(fields), column=1, pady=10, sticky="e")
        form_frame.grid_columnconfigure(1, weight=1)

    def open_supply_form(self, edit=False):
        s_data = get_supply_by_id(self.selected_supply_id) if edit else None
        form = tk.Toplevel(self.root)
        form.title("Edit Supply" if edit else "Add Supply")
        form.geometry("400x300")
        form.config(bg=BACKGROUND_COLOR)
        
        form_frame = ttk.Frame(form, padding=10, style='TFrame')
        form_frame.pack(fill="both", expand=True)

        fields = ["Name", "Price", "Purchase Link", "Quantity"]
        entries = {}
        for i, field in enumerate(fields):
            ttk.Label(form_frame, text=f"{field}:").grid(row=i, column=0, padx=5, pady=5, sticky="w")
            entry = ttk.Entry(form_frame, style='TEntry')
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            if edit and s_data:
                entry.insert(0, s_data[i+1])
            entries[field] = entry

        def save():
            data = [entries[f].get() for f in fields]
            if edit:
                update_supply(self.selected_supply_id, data)
            else:
                insert_supply(data)
            self.populate_supplies()
            form.destroy()

        ttk.Button(form_frame, text="Save", command=save, style='Accent.TButton').grid(row=len(fields), column=1, pady=10, sticky="e")
        form_frame.grid_columnconfigure(1, weight=1)

    def open_oil_form(self, edit=False):
        o_data = get_oil_by_id(self.selected_oil_id) if edit else None
        form = tk.Toplevel(self.root)
        form.title("Edit Oil" if edit else "Add Oil")
        form.geometry("400x300")
        form.config(bg=BACKGROUND_COLOR)
        
        form_frame = ttk.Frame(form, padding=10, style='TFrame')
        form_frame.pack(fill="both", expand=True)

        fields = ["Name", "Size(ml)", "Price", "Purchase Link", "Quantity"]
        entries = {}
        for i, field in enumerate(fields):
            ttk.Label(form_frame, text=f"{field}:").grid(row=i, column=0, padx=5, pady=5, sticky="w")
            entry = ttk.Entry(form_frame, style='TEntry')
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            if edit and o_data:
                entry.insert(0, o_data[i+1])
            entries[field] = entry

        def save():
            data = [entries[f].get() for f in fields]
            if edit:
                update_oil(self.selected_oil_id, data)
            else:
                insert_oil(data)
            self.populate_oils()
            form.destroy()

        ttk.Button(form_frame, text="Save", command=save, style='Accent.TButton').grid(row=len(fields), column=1, pady=10, sticky="e")
        form_frame.grid_columnconfigure(1, weight=1)

    def search_fragrance(self):
        query = self.search_entry.get()
        self.populate_table(self.men_tree, "Men", query)
        self.populate_table(self.women_tree, "Women", query)
        self.populate_table(self.unisex_tree, "Unisex", query)

    def refresh_all_tables(self):
        self.populate_table(self.men_tree, "Men")
        self.populate_table(self.women_tree, "Women")
        self.populate_table(self.unisex_tree, "Unisex")
        self.populate_customers()
        self.populate_sales()
        self.populate_supplies()
        self.populate_oils()
        if not self.selected_id or not get_fragrance_by_id(self.selected_id):
            self.update_fragrance_viewer(None)

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    # Ensure directories exist and create placeholder images if missing
    if not os.path.exists('assets'):
        os.makedirs('assets')
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)
        
    try:
        # Create mock image files for the viewer to work
        if not os.path.exists(LOGO_PATH):
            Image.new('RGB', (250, 200), color = PRIMARY_COLOR).save(LOGO_PATH)
        if not os.path.exists(f"{IMAGE_DIR}/placeholder.png"):
            Image.new('RGB', VIEWER_IMAGE_SIZE, color = (200, 200, 200)).save(f"{IMAGE_DIR}/placeholder.png")
    except Exception as e:
        print(f"Warning: Could not create mock image files. Ensure PIL is installed and permissions are correct. Error: {e}")

    root = tk.Tk()
    app = FragranceManagerApp(root)
    root.mainloop()