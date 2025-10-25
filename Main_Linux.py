import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import os
from datetime import datetime

# =========================================================================
# 📌 IMPORT DATABASE (Assumes database.py is in the same directory)
# =========================================================================
# NOTE: The actual content of database.py is omitted here for brevity 
# but must be present for the script to run.
from database import (
    init_db, get_fragrance_by_id, get_all_fragrances_by_gender, update_fragrance, 
    delete_fragrance, insert_fragrance, update_fragrance_quantity, 
    get_all_customers, get_customer_by_id, update_customer, delete_customer, 
    insert_customer, get_all_sales, insert_sale, 
    get_all_supplies, get_supply_by_id, update_supply, delete_supply, 
    insert_supply, get_all_oils, get_oil_by_id, update_oil, delete_oil, 
    insert_oil
) 

# --- STYLING CONSTANTS (MODERN DARK THEME) ---
PRIMARY_COLOR = "#00BFFF"          # Deep Sky Blue for primary actions/accents
ACCENT_COLOR = "#FF6347"           # Tomato Red for highlights/hover
BACKGROUND_COLOR = "#121212"       # Very Dark Background (OLED Black)
SECONDARY_BACKGROUND = "#1E1E1E"   # Slightly lighter background for frames
FOREGROUND_COLOR = "#E0E0E0"       # Light Gray for main text
BUTTON_BG_COLOR = "#333333"        # Dark Gray buttons
BUTTON_HOVER_COLOR = "#444444"     # Button hover effect
DANGER_COLOR = "#8B0000"           # Dark Red for destructive actions
TREEVIEW_BG = "#1E1E1E"            # Table background
VIEWER_IMAGE_SIZE = (180, 180) 
LOGO_PATH = "assets/logo.png"
IMAGE_DIR = "assets/images/" 
LOW_STOCK_THRESHOLD = 5

# =========================================================================
# I. CONTROLLER CLASS (LOGIC)
# =========================================================================

class FragranceController:
    """Handles all business logic and database interaction."""
    def __init__(self):
        init_db()

    # --- FRAGRANCE METHODS ---
    def get_fragrances_for_display(self, gender, query=None):
        fragrances = get_all_fragrances_by_gender(gender)
        display_data = []
        for f in fragrances:
            if query:
                q = query.lower()
                if q not in (f[1] or "").lower() and q not in (f[7] or "").lower():
                    continue
            
            try:
                unit_cost = float(f[5])
                sale_price = float(f[6])
                quantity = int(f[8])
            except (TypeError, ValueError):
                unit_cost, sale_price, quantity = 0.0, 0.0, 0
                
            total_cost = unit_cost * quantity
            retail_value = sale_price * quantity
            
            row_data = (
                str(f[0]), # ID for IID
                str(f[1] or ""), # Name
                str(f[7] or ""), # Inspired By
                f"{unit_cost:.2f}",
                f"{sale_price:.2f}",
                str(quantity),
                f"{total_cost:.2f}",
                f"{retail_value:.2f}",
                str(f[3] or "") # Gender
            )
            # LOW STOCK TAG APPLICATION
            tags = ("low_stock",) if quantity < LOW_STOCK_THRESHOLD else ()
            display_data.append((row_data, tags))
        return display_data

    def save_fragrance(self, fid, data, is_edit):
        if not data[0] or not data[2]:
            messagebox.showerror("Error", "Name and Gender are required.")
            return False
            
        try:
            if is_edit:
                update_fragrance(fid, data)
            else:
                insert_fragrance(data)
            return True
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to save fragrance: {e}")
            return False

    def delete_fragrance(self, fid):
        delete_fragrance(fid)

    def get_fragrance_details(self, fid):
        return get_fragrance_by_id(fid)

    # --- CUSTOMER METHODS ---
    def get_all_customers_for_display(self):
        return [(str(c[0]),) + c[1:] for c in get_all_customers()]

    def get_customer_options(self):
        return [f"{c[1]} (ID:{c[0]})" for c in get_all_customers()]

    def save_customer(self, cid, data, is_edit):
        try:
            if is_edit:
                update_customer(cid, data)
            else:
                insert_customer(data)
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to save customer: {e}")

    def delete_customer(self, cid):
        delete_customer(cid)
        
    def get_customer_details(self, cid):
        return get_customer_by_id(cid)

    # --- SALE METHODS ---
    def get_all_sales_for_display(self):
        return [(str(s[0]),) + s[1:] for s in get_all_sales()]

    def record_sale(self, selected_fragrance_id, customer_str, qty_str):
        try:
            qty = int(qty_str)
            if qty <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a positive integer.")
            return False

        fragrance = self.get_fragrance_details(selected_fragrance_id)
        if not fragrance:
            messagebox.showerror("Error", "Fragrance not found.")
            return False

        current_qty = int(fragrance[8])
        if qty > current_qty:
            messagebox.showerror("Error", f"Not enough stock. Available: {current_qty}")
            return False
            
        try:
            customer_id = int(customer_str.split("ID:")[1].replace(")", ""))
        except:
            messagebox.showerror("Error", "Invalid customer selection format.")
            return False
        
        unit_cost = float(fragrance[5])
        sale_price = float(fragrance[6])
        revenue = sale_price * qty
        profit = (sale_price - unit_cost) * qty
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            insert_sale((selected_fragrance_id, customer_id, qty, unit_cost, sale_price, revenue, profit, date))
            update_fragrance_quantity(selected_fragrance_id, current_qty - qty)
            messagebox.showinfo("Success", f"Recorded sale of {qty} units of {fragrance[1]}.")
            return True
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to record sale: {e}")
            return False
    
    # --- SUPPLY/OIL METHODS ---
    def get_all_supplies_for_display(self):
        return [(str(s[0]),) + s[1:] for s in get_all_supplies()]
    
    def get_supply_details(self, sid):
        return get_supply_by_id(sid)
        
    def save_supply(self, sid, data, is_edit):
        try:
            if is_edit: update_supply(sid, data)
            else: insert_supply(data)
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to save supply: {e}")
    
    def delete_supply(self, sid):
        delete_supply(sid)

    def get_all_oils_for_display(self):
        return [(str(o[0]),) + o[1:] for o in get_all_oils()]
    
    def get_oil_details(self, oid):
        return get_oil_by_id(oid)

    def save_oil(self, oid, data, is_edit):
        try:
            if is_edit: update_oil(oid, data)
            else: insert_oil(data)
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to save oil: {e}")

    def delete_oil(self, oid):
        delete_oil(oid)

# =========================================================================
# III. VALIDATION CLASS
# =========================================================================

class NumericValidator:
    """Helper class for validating numeric inputs."""
    def __init__(self, master):
        self.vcmd_float = master.register(self._validate_float)
        self.vcmd_int = master.register(self._validate_int)

    def _validate_float(self, P):
        """Allows empty string, a single dot, or valid float format."""
        if P == "" or P == ".":
            return True
        try:
            float(P)
            return True
        except ValueError:
            return False
            
    def _validate_int(self, P):
        """Allows empty string or valid positive integer format."""
        if P == "":
            return True
        # Allow only positive integers
        if P.isdigit() and int(P) >= 0:
            return True
        return False

# =========================================================================
# II. VIEW CLASS (GUI - MODERN DARK THEME)
# =========================================================================

# --- BASE CLASS FOR REPETITIVE TAB SETUP (Template) ---
class BaseInventoryTab(ttk.Frame):
    def __init__(self, parent, app, columns, select_callback, populate_method):
        super().__init__(parent, style='TFrame')
        self.app = app
        self.columns = columns
        self.populate_method = populate_method
        self.item_type = columns[0] if len(columns) > 0 else "Item"
        self.selected_id_var = tk.StringVar(value=None) 
        self.tree = self._setup_table()
        self.tree.bind("<<TreeviewSelect>>", select_callback)
        self.populate_table()

    def _setup_table(self):
        table_frame = ttk.Frame(self, style='TFrame')
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        tree_columns = [f"#{i}" for i in range(1, len(self.columns) + 1)]
        tree = ttk.Treeview(table_frame, columns=tree_columns, show="headings", selectmode="browse") 

        for i, col_name in enumerate(self.columns):
            tree.heading(tree_columns[i], text=col_name)
            tree.column(tree_columns[i], width=120, anchor="center")
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # 🟢 FIX: Configure the low_stock tag directly on the Treeview widget
        # We use only tag_configure as tag_map is not supported by your Tkinter version.
        # This will apply the OrangeRed background when the row is NOT selected.
        tree.tag_configure("low_stock", background="OrangeRed", foreground="white")
        
        return tree

    def populate_table(self, data=None):
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        if data is None:
            data = self.populate_method()
            
        for item in data:
            if isinstance(item, tuple) and len(item) == 2 and isinstance(item[1], tuple):
                row_values, tags = item
            else:
                row_values = item
                tags = ()

            self.tree.insert("", "end",
                            iid=row_values[0],
                            values=row_values[1:], 
                            tags=tags)

    def get_selected_id(self):
        selected = self.tree.selection()
        if not selected:
            return None
        try:
            # iid is the actual ID from the database (the first column value)
            return int(selected[0]) 
        except ValueError:
            return None


# --- MAIN APPLICATION CLASS ---
class FragranceManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LJ Fragrances Manager")
        self.root.geometry("1600x900")
        
        self.controller = FragranceController()
        self.selected_fragrance_id = None
        self.validator = NumericValidator(root) # Initialize Validator
        
        self.setup_ui()
        self.refresh_all_tables()

    def setup_ui(self):
        style = ttk.Style()
        # Use the clam theme as it supports more advanced styling like borders/padding
        style.theme_use("clam") 
        self.root.config(bg=BACKGROUND_COLOR)
        
        # --- MODERN DARK THEME STYLING DEFINITION ---
        
        # 1. Base Styles
        style.configure("TFrame", background=BACKGROUND_COLOR)
        style.configure("TLabel", background=BACKGROUND_COLOR, foreground=FOREGROUND_COLOR, font=('Arial', 10))
        style.configure("TLabelFrame", background=BACKGROUND_COLOR, foreground=PRIMARY_COLOR, borderwidth=0)
        style.configure("TLabelFrame.Label", background=BACKGROUND_COLOR, foreground=PRIMARY_COLOR, font=('Arial', 12, 'bold'))
        
        # 2. Rounded Button Style (Requires assets/button_normal.png from PIL)
        try:
            # 📌 Use absolute path to ensure image is found regardless of execution directory
            button_image_path = os.path.abspath("assets/button_normal.png")
            style.element_create("Rounded.Button.border", "image", button_image_path, border=4, sticky="nswe")
            
            style.layout("Rounded.TButton",
                [('Rounded.Button.border', {'sticky': 'nswe', 'border': 
                    [('Rounded.Button.padding', {'sticky': 'nswe', 'children':
                        [('Rounded.Button.label', {'sticky': 'nswe'})]})]})])

            style.configure("Rounded.TButton", 
                font=('Arial', 10, 'bold'), 
                padding=8, 
                relief="flat", 
                background=BUTTON_BG_COLOR, 
                foreground=FOREGROUND_COLOR, 
                borderwidth=0, 
                focusthickness=0)
                
            style.map("Rounded.TButton",
                background=[('active', BUTTON_HOVER_COLOR), ('pressed', PRIMARY_COLOR)], 
                foreground=[('pressed', 'white')])

            style.configure("Accent.Rounded.TButton", 
                background=PRIMARY_COLOR, 
                foreground="white")
            style.map("Accent.Rounded.TButton",
                background=[('active', ACCENT_COLOR), ('pressed', PRIMARY_COLOR)])

            style.configure("Danger.Rounded.TButton", 
                background=DANGER_COLOR, 
                foreground="white")
            style.map("Danger.Rounded.TButton",
                background=[('active', ACCENT_COLOR), ('pressed', DANGER_COLOR)])
        except tk.TclError as e:
             # Fallback to standard button style if image fails (as indicated by your output)
            print(f"Warning: Custom button style failed. Falling back to default. Error: {e}")
            style.configure("Rounded.TButton", font=('Arial', 10, 'bold'), padding=8, relief="flat", background=BUTTON_BG_COLOR, foreground=FOREGROUND_COLOR)
            style.configure("Accent.Rounded.TButton", background=PRIMARY_COLOR, foreground="white")
            style.configure("Danger.Rounded.TButton", background=DANGER_COLOR, foreground="white")


        # 3. Notebook/Tab Styles
        style.configure("TNotebook", background=BACKGROUND_COLOR, borderwidth=0)
        style.configure("TNotebook.Tab", 
            padding=[15, 5], 
            background=SECONDARY_BACKGROUND, # Subtle background for inactive tabs
            foreground=FOREGROUND_COLOR, 
            font=('Arial', 10))
        style.map("TNotebook.Tab", 
            background=[('selected', PRIMARY_COLOR)], # Highlight selected tab
            foreground=[('selected', 'white')])

        # 4. Treeview Styles
        style.configure("Treeview.Heading", 
            font=('Arial', 10, 'bold'), 
            background=SECONDARY_BACKGROUND, 
            foreground=PRIMARY_COLOR, 
            relief="flat", 
            padding=[5, 10])
        style.configure("Treeview", 
            background=TREEVIEW_BG, 
            foreground=FOREGROUND_COLOR, 
            fieldbackground=TREEVIEW_BG, 
            font=('Arial', 10), 
            rowheight=28, 
            borderwidth=0)
        # This map applies to regular rows when selected
        style.map("Treeview", 
            background=[('selected', PRIMARY_COLOR)], 
            foreground=[('selected', 'white')])
            
        # 5. Low Stock Tag Configuration removed from here (Fixed in BaseInventoryTab)

        # 6. Entry/Combobox Styles
        style.configure("TEntry", 
            padding=5, 
            fieldbackground=SECONDARY_BACKGROUND, 
            foreground=FOREGROUND_COLOR, 
            bordercolor="#333333", 
            relief="flat", 
            insertcolor=PRIMARY_COLOR)
        style.configure("TCombobox", 
            padding=5, 
            fieldbackground=SECONDARY_BACKGROUND, 
            foreground=FOREGROUND_COLOR, 
            bordercolor="#333333", 
            relief="flat")


        main_frame = ttk.Frame(self.root, style='TFrame') 
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # Top Frame has secondary background for depth
        top_frame = ttk.Frame(main_frame, style='TFrame')
        top_frame.pack(fill="x", pady=5)
        
        self.load_logo(top_frame)
        self._setup_search(top_frame)
        self._setup_viewer(top_frame)

        self.tabControl = ttk.Notebook(main_frame)
        self.tabControl.pack(expand=1, fill="both", pady=10)

        self._setup_tabs()

    def load_logo(self, parent_frame):
        # Using os.path.abspath for robust path handling
        logo_full_path = os.path.abspath(LOGO_PATH)
        if os.path.exists(logo_full_path):
            try:
                img = Image.open(logo_full_path).resize((250, 200)) 
                self.logo_photo = ImageTk.PhotoImage(img)
                logo_frame = ttk.Frame(parent_frame, style='TFrame')
                logo_frame.pack(side="left", padx=20, anchor="n")
                logo_label = ttk.Label(logo_frame, image=self.logo_photo, style='TLabel')
                logo_label.pack(side="top")
            except Exception:
                ttk.Label(parent_frame, text="LJ Fragrances", font=('Arial', 18, 'bold'), style='TLabel').pack(side="left", padx=20, anchor="n")
        else:
            ttk.Label(parent_frame, text="LJ Fragrances", font=('Arial', 18, 'bold'), style='TLabel').pack(side="left", padx=20, anchor="n")

    def _setup_search(self, parent):
        search_container = ttk.Frame(parent, style='TFrame')
        search_container.pack(side="left", padx=5, fill="y", expand=False)
        search_frame = ttk.Frame(search_container, style='TFrame')
        search_frame.pack(side="top", anchor="w", pady=(10, 0))

        ttk.Label(search_frame, text="🔍 Search Fragrance:").pack(side="left", padx=5)
        self.search_entry = ttk.Entry(search_frame, width=30, style='TEntry')
        self.search_entry.pack(side="left", padx=5)
        ttk.Button(search_frame, text="Search", command=self.search_fragrance, style='Rounded.TButton').pack(side="left", padx=5)
        ttk.Button(search_frame, text="Clear", command=self.clear_search, style='Rounded.TButton').pack(side="left", padx=5)
        
    def _setup_viewer(self, parent):
        # Use LabelFrame for a visual grouping effect
        self.image_viewer_frame = ttk.LabelFrame(parent, text="Fragrance Details", padding="10")
        self.image_viewer_frame.pack(side="right", fill="y", padx=20, anchor="n") 
        
        # Use secondary background for image area
        self.image_label = ttk.Label(self.image_viewer_frame, anchor="center", background=SECONDARY_BACKGROUND, borderwidth=1, relief="solid")
        self.image_label.grid(row=0, column=0, padx=5, pady=5)
        
        # Use secondary background for details area
        self.detail_text_label = tk.Label(self.image_viewer_frame, justify=tk.LEFT, text="Select a fragrance to view details.", width=35, anchor="nw", background=SECONDARY_BACKGROUND, fg=FOREGROUND_COLOR, font=('Arial', 10))
        self.detail_text_label.grid(row=0, column=1, padx=10, pady=5, sticky="nsw")

    def _setup_tabs(self):
        FRAG_COLS = ("Name", "Inspired By", "Unit Cost", "Sale Price", "Quantity", "Total Cost", "Retail Value", "Gender")
        self.men_tab = BaseInventoryTab(self.tabControl, self, FRAG_COLS, self.on_fragrance_select, lambda: self.controller.get_fragrances_for_display("Men"))
        self.women_tab = BaseInventoryTab(self.tabControl, self, FRAG_COLS, self.on_fragrance_select, lambda: self.controller.get_fragrances_for_display("Women"))
        self.unisex_tab = BaseInventoryTab(self.tabControl, self, FRAG_COLS, self.on_fragrance_select, lambda: self.controller.get_fragrances_for_display("Unisex"))
        
        self.tabControl.add(self.men_tab, text="Men")
        self.tabControl.add(self.women_tab, text="Women")
        self.tabControl.add(self.unisex_tab, text="Unisex")
        self._setup_fragrance_buttons([self.men_tab, self.women_tab, self.unisex_tab])

        CUST_COLS = ("ID", "Name", "Email", "Phone", "City", "Reference")
        self.customer_tab = BaseInventoryTab(self.tabControl, self, CUST_COLS, self.on_customer_select, self.controller.get_all_customers_for_display)
        self.tabControl.add(self.customer_tab, text="Customers")
        self._setup_crud_buttons(self.customer_tab, self.add_customer, self.edit_customer, self.delete_customer)
        
        SUPPLY_COLS = ("ID", "Name", "Price", "Purchase Link", "Quantity")
        self.supplies_tab = BaseInventoryTab(self.tabControl, self, SUPPLY_COLS, self.on_supply_select, self.controller.get_all_supplies_for_display)
        self.tabControl.add(self.supplies_tab, text="Supplies")
        self._setup_crud_buttons(self.supplies_tab, self.add_supply, self.edit_supply, self.delete_supply)

        OIL_COLS = ("ID", "Name", "Size(ml)", "Price", "Purchase Link", "Quantity")
        self.oils_tab = BaseInventoryTab(self.tabControl, self, OIL_COLS, self.on_oil_select, self.controller.get_all_oils_for_display)
        self.tabControl.add(self.oils_tab, text="Oils")
        self._setup_crud_buttons(self.oils_tab, self.add_oil, self.edit_oil, self.delete_oil)

        SALES_COLS = ("ID", "Fragrance", "Customer", "Qty Sold", "Unit Cost", "Sale Price", "Revenue", "Profit", "Date")
        self.sales_tab = BaseInventoryTab(self.tabControl, self, SALES_COLS, lambda e: None, self.controller.get_all_sales_for_display)
        self.tabControl.add(self.sales_tab, text="Sales")


    def _setup_fragrance_buttons(self, tabs):
        for tab in tabs:
            btn_frame = ttk.Frame(tab, style='TFrame')
            btn_frame.pack(fill="x", pady=5, padx=5)
            ttk.Button(btn_frame, text="➕ Add Fragrance", command=self.add_fragrance, style='Accent.Rounded.TButton').pack(side="left", padx=5)
            ttk.Button(btn_frame, text="✏️ Edit Fragrance", command=self.edit_fragrance, style='Rounded.TButton').pack(side="left", padx=5)
            ttk.Button(btn_frame, text="🗑️ Delete Fragrance", command=self.delete_fragrance, style='Danger.Rounded.TButton').pack(side="left", padx=5)
            ttk.Button(btn_frame, text="💵 Record Sale", command=self.record_sale, style='Accent.Rounded.TButton').pack(side="right", padx=5)

    def _setup_crud_buttons(self, tab, add_cmd, edit_cmd, delete_cmd):
        btn_frame = ttk.Frame(tab, style='TFrame')
        btn_frame.pack(fill="x", pady=5, padx=5)
        ttk.Button(btn_frame, text=f"➕ Add {tab.item_type}", command=add_cmd, style='Accent.Rounded.TButton').pack(side="left", padx=5)
        ttk.Button(btn_frame, text=f"✏️ Edit {tab.item_type}", command=edit_cmd, style='Rounded.TButton').pack(side="left", padx=5)
        ttk.Button(btn_frame, text=f"🗑️ Delete {tab.item_type}", command=delete_cmd, style='Danger.Rounded.TButton').pack(side="left", padx=5)
    
    # --- SELECTION HANDLERS ---
    def on_fragrance_select(self, event):
        tab = self.tabControl.nametowidget(self.tabControl.select())
        self.selected_fragrance_id = tab.get_selected_id()
        self.update_fragrance_viewer(self.selected_fragrance_id)

    def on_customer_select(self, event):
        self.customer_tab.selected_id_var.set(self.customer_tab.get_selected_id())
    
    def on_supply_select(self, event):
        self.supplies_tab.selected_id_var.set(self.supplies_tab.get_selected_id())

    def on_oil_select(self, event):
        self.oils_tab.selected_id_var.set(self.oils_tab.get_selected_id())
        
    def update_fragrance_viewer(self, fid):
        if not fid:
            self.image_viewer_frame.config(text="Fragrance Details")
            self.image_label.config(image='', text="No Image", background=SECONDARY_BACKGROUND)
            self.detail_text_label.config(text="Select a fragrance to view details.")
            return

        f_data = self.controller.get_fragrance_details(fid)
        if not f_data: return

        _, name, desc, gender, _, unit_cost, sale_price, inspired_by, qty, img_path = f_data

        self.image_viewer_frame.config(text=name)

        details = (
            f"Name: {name}\n"
            f"Inspired By: {inspired_by}\n"
            f"Gender: {gender}\n"
            f"Cost: ${float(unit_cost):.2f} | Price: ${float(sale_price):.2f}\n"
            f"Stock: {qty}\n"
            f"\nDescription: {desc or 'N/A'}"
        )
        self.detail_text_label.config(text=details)

        if img_path and os.path.exists(img_path):
            try:
                # 📌 Use absolute path for loading the image
                img_full_path = os.path.abspath(img_path)
                img = Image.open(img_full_path).resize(VIEWER_IMAGE_SIZE) 
                photo = ImageTk.PhotoImage(img)
                self.current_fragrance_image = photo 
                self.image_label.config(image=self.current_fragrance_image, text="", background=SECONDARY_BACKGROUND)
            except Exception:
                self.image_label.config(text="Image Error", image='', background=SECONDARY_BACKGROUND)
        else:
            self.image_label.config(text="No Image", image='', background=SECONDARY_BACKGROUND)
        
    # --- CRUD Methods (Forms include validation hooks) ---
    def add_fragrance(self): self.open_fragrance_form()
    def edit_fragrance(self):
        if not self.selected_fragrance_id: messagebox.showwarning("No Selection", "Select fragrance to edit"); return
        self.open_fragrance_form(edit=True)
    def delete_fragrance(self):
        if not self.selected_fragrance_id: messagebox.showwarning("No Selection", "Select fragrance to delete"); return
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this fragrance?"):
            self.controller.delete_fragrance(self.selected_fragrance_id)
            self.refresh_all_tables()
            self.selected_fragrance_id = None
            self.update_fragrance_viewer(None)

    def add_customer(self): self.open_customer_form()
    def edit_customer(self):
        cid = self.customer_tab.selected_id_var.get()
        if not cid: messagebox.showwarning("No Selection", "Select customer to edit"); return
        self.open_customer_form(edit=True, cid=int(cid))
    def delete_customer(self):
        cid = self.customer_tab.selected_id_var.get()
        if not cid: messagebox.showwarning("No Selection", "Select customer to delete"); return
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this customer?"):
            self.controller.delete_customer(int(cid))
            self.refresh_all_tables()

    def add_supply(self): self.open_supply_form()
    def edit_supply(self):
        sid = self.supplies_tab.selected_id_var.get()
        if not sid: messagebox.showwarning("No Selection", "Select supply to edit"); return
        self.open_supply_form(edit=True, sid=int(sid))
    def delete_supply(self):
        sid = self.supplies_tab.selected_id_var.get()
        if not sid: messagebox.showwarning("No Selection", "Select supply to delete"); return
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this supply?"):
            self.controller.delete_supply(int(sid))
            self.refresh_all_tables()
            
    def add_oil(self): self.open_oil_form()
    def edit_oil(self):
        oid = self.oils_tab.selected_id_var.get()
        if not oid: messagebox.showwarning("No Selection", "Select oil to edit"); return
        self.open_oil_form(edit=True, oid=int(oid))
    def delete_oil(self):
        oid = self.oils_tab.selected_id_var.get()
        if not oid: messagebox.showwarning("No Selection", "Select oil to delete"); return
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this oil?"):
            self.controller.delete_oil(int(oid))
            self.refresh_all_tables()


    def record_sale(self):
        if not self.selected_fragrance_id:
            messagebox.showwarning("No Selection", "Select a fragrance to record a sale.")
            return
        
        customers = self.controller.get_customer_options()
        if not customers:
            messagebox.showwarning("No Customers", "No customers found. Please add a customer first.")
            return
        
        form = tk.Toplevel(self.root)
        form.title("Record Sale")
        form.geometry("400x300")
        form.config(bg=BACKGROUND_COLOR)
        
        form_frame = ttk.Frame(form, padding=10, style='TFrame')
        form_frame.pack(fill="both", expand=True)

        ttk.Label(form_frame, text="Customer:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        customer_var = tk.StringVar()
        cust_combo = ttk.Combobox(form_frame, values=customers, textvariable=customer_var, state="readonly", style='TCombobox')
        cust_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(form_frame, text="Quantity:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        # 📌 VALIDATION: Integer for quantity
        qty_entry = ttk.Entry(form_frame, style='TEntry', validate='key', validatecommand=(self.validator.vcmd_int, '%P'))
        qty_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        def save_sale():
            if not customer_var.get(): messagebox.showwarning("Error", "Select customer"); return
            if self.controller.record_sale(self.selected_fragrance_id, customer_var.get(), qty_entry.get()):
                self.refresh_all_tables()
                self.update_fragrance_viewer(self.selected_fragrance_id)
                form.destroy()
        
        ttk.Button(form_frame, text="Save Sale", command=save_sale, style='Accent.Rounded.TButton').grid(row=2, column=1, pady=10, sticky="e")
        form_frame.grid_columnconfigure(1, weight=1)

    def open_fragrance_form(self, edit=False):
        fid = self.selected_fragrance_id if edit else None
        f_data = self.controller.get_fragrance_details(fid) if edit else None
        
        form = tk.Toplevel(self.root)
        form.title("Edit Fragrance" if edit else "Add Fragrance")
        form.geometry("450x450")
        form.config(bg=BACKGROUND_COLOR)
        form_frame = ttk.Frame(form, padding=10, style='TFrame')
        form_frame.pack(fill="both", expand=True)

        fields = ["Name", "Description", "Gender", "Category", "Unit Cost", "Sale Price", "Inspired By", "Quantity", "Image"]
        entries = {}

        for i, field in enumerate(fields):
            ttk.Label(form_frame, text=f"{field}:").grid(row=i, column=0, padx=5, pady=5, sticky="w")
            
            if field == "Gender":
                entry = ttk.Combobox(form_frame, values=["Men", "Women", "Unisex"], state="readonly", style='TCombobox')
                if edit and f_data and len(f_data) > i+1: entry.set(f_data[i+1])
            elif field in ["Unit Cost", "Sale Price"]:
                # 📌 VALIDATION: Float for costs/prices
                entry = ttk.Entry(form_frame, width=30, style='TEntry', validate='key', validatecommand=(self.validator.vcmd_float, '%P'))
                if edit and f_data and len(f_data) > i+1: entry.insert(0, f_data[i+1])
            elif field == "Quantity":
                # 📌 VALIDATION: Integer for quantity
                entry = ttk.Entry(form_frame, width=30, style='TEntry', validate='key', validatecommand=(self.validator.vcmd_int, '%P'))
                if edit and f_data and len(f_data) > i+1: entry.insert(0, f_data[i+1])
            else:
                entry = ttk.Entry(form_frame, width=30, style='TEntry')
                if edit and f_data and len(f_data) > i+1: entry.insert(0, f_data[i+1])
                
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            entries[field] = entry

        ttk.Button(form_frame, text="Choose Image", command=lambda: self.choose_image(entries["Image"]), style='Rounded.TButton').grid(row=8, column=2, padx=5)
        
        def save():
            data = [entries[f].get() for f in fields]
            if self.controller.save_fragrance(fid, data, edit):
                self.refresh_all_tables()
                self.update_fragrance_viewer(fid)
                form.destroy()

        ttk.Button(form_frame, text="Save", command=save, style='Accent.Rounded.TButton').grid(row=9, column=1, pady=15, sticky="e")
        form_frame.grid_columnconfigure(1, weight=1)

    def open_customer_form(self, edit=False, cid=None):
        c_data = self.controller.get_customer_details(cid) if edit else None
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
            if edit and c_data and len(c_data) > i+1: entry.insert(0, c_data[i+1])
            entries[field] = entry
            
        def save():
            data = [entries[f].get() for f in fields]
            self.controller.save_customer(cid, data, edit)
            self.refresh_all_tables()
            form.destroy()

        ttk.Button(form_frame, text="Save", command=save, style='Accent.Rounded.TButton').grid(row=len(fields), column=1, pady=10, sticky="e")
        form_frame.grid_columnconfigure(1, weight=1)
        
    def open_supply_form(self, edit=False, sid=None):
        s_data = self.controller.get_supply_details(sid) if edit else None
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
            
            if field == "Price":
                # 📌 VALIDATION: Float for price
                entry = ttk.Entry(form_frame, style='TEntry', validate='key', validatecommand=(self.validator.vcmd_float, '%P'))
            elif field == "Quantity":
                # 📌 VALIDATION: Integer for quantity
                entry = ttk.Entry(form_frame, style='TEntry', validate='key', validatecommand=(self.validator.vcmd_int, '%P'))
            else:
                entry = ttk.Entry(form_frame, style='TEntry')
            
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            if edit and s_data and len(s_data) > i+1: entry.insert(0, s_data[i+1])
            entries[field] = entry

        def save():
            data = [entries[f].get() for f in fields]
            self.controller.save_supply(sid, data, edit)
            self.refresh_all_tables()
            form.destroy()

        ttk.Button(form_frame, text="Save", command=save, style='Accent.Rounded.TButton').grid(row=len(fields), column=1, pady=10, sticky="e")
        form_frame.grid_columnconfigure(1, weight=1)

    def open_oil_form(self, edit=False, oid=None):
        o_data = self.controller.get_oil_details(oid) if edit else None
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
            
            if field in ["Size(ml)", "Price"]:
                # 📌 VALIDATION: Float for size/price
                entry = ttk.Entry(form_frame, style='TEntry', validate='key', validatecommand=(self.validator.vcmd_float, '%P'))
            elif field == "Quantity":
                # 📌 VALIDATION: Integer for quantity
                entry = ttk.Entry(form_frame, style='TEntry', validate='key', validatecommand=(self.validator.vcmd_int, '%P'))
            else:
                entry = ttk.Entry(form_frame, style='TEntry')
            
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            if edit and o_data and len(o_data) > i+1: entry.insert(0, o_data[i+1])
            entries[field] = entry

        def save():
            data = [entries[f].get() for f in fields]
            self.controller.save_oil(oid, data, edit)
            self.refresh_all_tables()
            form.destroy()

        ttk.Button(form_frame, text="Save", command=save, style='Accent.Rounded.TButton').grid(row=len(fields), column=1, pady=10, sticky="e")
        form_frame.grid_columnconfigure(1, weight=1)
        
    # --- UTILITY ---
    def choose_image(self, entry_widget):
        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files","*.png *.jpg *.jpeg *.gif *.bmp"),("All files","*.*")]
        )
        if path:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, path)
            
    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.refresh_all_tables()

    def search_fragrance(self):
        query = self.search_entry.get()
        if not query:
            self.refresh_all_tables()
            return
            
        active_tab_name = self.tabControl.tab(self.tabControl.select(), "text")
        
        if active_tab_name == "Men":
            data = self.controller.get_fragrances_for_display("Men", query)
            self.men_tab.populate_table(data)
        elif active_tab_name == "Women":
            data = self.controller.get_fragrances_for_display("Women", query)
            self.women_tab.populate_table(data)
        elif active_tab_name == "Unisex":
            data = self.controller.get_fragrances_for_display("Unisex", query)
            self.unisex_tab.populate_table(data)
        else:
            messagebox.showinfo("Search", "Search only applies to Fragrance tabs.")

    def refresh_all_tables(self):
        """Refreshes all tables by calling the populate method on each tab instance."""
        tabs = [self.men_tab, self.women_tab, self.unisex_tab, self.customer_tab, self.sales_tab, self.supplies_tab, self.oils_tab]
        for tab in tabs:
            tab.populate_table() 
        
        if not self.selected_fragrance_id or not self.controller.get_fragrance_details(self.selected_fragrance_id):
            self.update_fragrance_viewer(None)

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    # Get the directory where the script is located and change the CWD
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Change the current directory to the script's directory for reliable pathing
    os.chdir(script_dir) 
    
    # Setup directories for assets and images
    if not os.path.exists('assets'): os.makedirs('assets')
    if not os.path.exists(IMAGE_DIR): os.makedirs(IMAGE_DIR)

    # Create placeholder images/assets if they don't exist
    try:
        # Simple rounded-rectangle image for custom button style
        img_button = Image.new('RGBA', (60, 30), color=(51, 51, 51, 255))
        draw = ImageDraw.Draw(img_button)
        draw.rounded_rectangle((0, 0, 60, 30), radius=10, fill=(51, 51, 51, 255))
        # Save the asset using the full path now that we are in the correct directory
        img_button.save(os.path.join(script_dir, "assets/button_normal.png"))

        if not os.path.exists(os.path.join(script_dir, LOGO_PATH)):
            Image.new('RGB', (250, 200), color = PRIMARY_COLOR).save(os.path.join(script_dir, LOGO_PATH))
        if not os.path.exists(os.path.join(script_dir, f"{IMAGE_DIR}/placeholder.png")):
            Image.new('RGB', VIEWER_IMAGE_SIZE, color = (50, 50, 50)).save(os.path.join(script_dir, f"{IMAGE_DIR}/placeholder.png"))
    except Exception as e:
        # This warning remains, but the code will now fall back to default buttons.
        print(f"Warning: Could not create mock image files. Ensure you have Pillow installed (`pip install Pillow`). Error: {e}")

    root = tk.Tk()
    app = FragranceManagerApp(root)
    root.mainloop()