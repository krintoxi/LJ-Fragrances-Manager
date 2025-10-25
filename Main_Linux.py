import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime # Used for date handling in sales and expense logic

# NOTE: database.py must be present in the same directory
from database import (
    # CONNECTION & SETUP
    get_conn,
    init_db,
    
    # FRAGRANCE FUNCTIONS
    insert_fragrance,
    get_all_fragrances,
    get_all_fragrances_by_gender,
    get_fragrance_by_id,
    get_fragrance_by_name,
    update_fragrance,
    delete_fragrance,
    update_fragrance_quantity,
    
    # CUSTOMER FUNCTIONS
    insert_customer,
    get_all_customers,
    get_customer_by_id,
    update_customer,
    delete_customer,
    
    # SALES FUNCTIONS
    insert_sale,
    get_all_sales,
    get_sales_by_month, 
    
    # SUPPLIES FUNCTIONS
    insert_supply,
    get_all_supplies,
    get_supply_by_id,
    get_supply_by_name,
    update_supply,
    delete_supply,
    
    # OIL FUNCTIONS
    insert_oil,
    get_all_oils,
    get_oil_by_id,
    get_oil_by_name,
    update_oil,
    delete_oil,
    
    # EXPENSE FUNCTIONS
    insert_expense,
    get_all_expenses,
    get_expense_by_id,
)

# --- NEW STYLING CONSTANTS (MODERN LIGHT THEME) ---
PRIMARY_ACCENT = "#007ACC"          # Blue for primary actions/accents
BG_LIGHT = "#FFFFFF"                # White/Light Gray for main background
BG_SECONDARY = "#F0F0F0"            # Very Light Gray for frames/inputs
FONT_COLOR = "#333333"              # Dark Gray for main text
BORDER_COLOR = "#CCCCCC"            # Light border color
LOW_STOCK_COLOR = "#FF6347"          # Red/Orange for low stock warning

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
        
        # Treeview References
        self.men_tree = None
        self.women_tree = None
        self.unisex_tree = None
        self.customer_tree = None
        self.sales_tree = None
        self.supplies_tree = None
        self.oils_tree = None
        self.expenses_tree = None
        self.chart_canvas_container = None
        
        self.month_var = tk.StringVar(value="All Months")
        self.sales_month_var = tk.StringVar(value="All Months")
        self.total_expense_label = None

        init_db()
        # Ensure image directory exists
        if not os.path.exists(IMAGE_DIR):
            os.makedirs(IMAGE_DIR)

        self.setup_ui()
        self.refresh_all_tables() # Initial population

    # ---------------- UTILITY: VALIDATION ----------------
    def validate_numeric_input(self, value, field_name, is_integer=False):
        """Checks if a string can be converted to a number, returning None on failure."""
        value = str(value).strip()
        
        if not value or value.isspace():
            return 0 if is_integer else 0.0 # Treat empty/whitespace numeric fields as zero
        
        try:
            # Attempt to clean up currency formatting if it's accidentally passed
            if isinstance(value, str):
                value = value.replace('$', '').replace(',', '')
                
            if is_integer:
                result = int(value)
            else:
                result = float(value)
            
            if result < 0:
                messagebox.showerror("Input Error", f"The value for '{field_name}' must be zero or positive.")
                return None
                
            return result
        except ValueError:
            type_str = "an integer" if is_integer else "a number (e.g., 10.50)"
            messagebox.showerror("Input Error", f"The value entered for '{field_name}' is not a valid {type_str}. Please use only digits and an optional decimal point.")
            return None 
            
    def refresh_all_tables(self):
        # Refresh logic
        self.populate_table(self.men_tree, "Men")
        self.populate_table(self.women_tree, "Women")
        self.populate_table(self.unisex_tree, "Unisex")
        self.populate_customers()
        self.populate_sales()
        self.populate_supplies()
        self.populate_oils()
        self.populate_expenses()
        self.update_fragrance_viewer(self.selected_id)

    # ---------------- FRAGRANCE LOGIC ----------------
    def populate_table(self, tree, gender):
        """Populates the fragrance treeview, applying the low stock tag."""
        if not tree: return
        for row in tree.get_children():
            tree.delete(row)
        
        fragrances = get_all_fragrances_by_gender(gender)
        
        for i, f in enumerate(fragrances):
            tags = ()
            quantity = int(f[8] or 0) # f[8] is quantity
            if quantity <= 5: 
                tags = ('low_stock',)
                
            # f is: (id, name, desc, gender, cat, u_cost, s_price, inspired, qty, img_path)
            tree.insert("", "end", iid=str(f[0]), tags=tags, 
                                values=(f[0], f[1], f[3], f[4], f"{f[5]:.2f}", f"{f[6]:.2f}", f[7], quantity))

    def update_fragrance_viewer(self, fid):
        """Loads and displays the image and details for the selected fragrance ID."""
        if fid is None or fid == 0:
            self.image_label.config(image='')
            self.image_label.image = None
            self.detail_text_label.config(text="Select a fragrance to view details.")
            return
            
        fragrance = get_fragrance_by_id(fid)
        if not fragrance: return
        
        # Display details (indexes based on your DB tuple structure)
        details = (
            f"ID: {fragrance[0]}\n"
            f"Name: {fragrance[1]}\n"
            f"Category: {fragrance[4]}\n"
            f"Unit Cost: ${fragrance[5]:.2f}\n"
            f"Sale Price: ${fragrance[6]:.2f}\n"
            f"Stock: {fragrance[8]}\n"
            f"Inspired By: {fragrance[7]}"
        )
        self.detail_text_label.config(text=details)
        
        # Image loading logic (assumes image path is at index 9)
        image_path = fragrance[9]
        if image_path and os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                img = img.resize(VIEWER_IMAGE_SIZE, Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.image_label.config(image=photo)
                self.image_label.image = photo
            except Exception as e:
                print(f"Error loading image: {e}")
                self.image_label.config(image='')
                self.image_label.image = None
        else:
            self.image_label.config(image='')
            self.image_label.image = None

    def on_fragrance_select(self, event):
        tree = event.widget
        selected_item = tree.focus()
        if selected_item:
            # FIX: selected_item IS the iid (the ID from the database)
            self.selected_id = int(selected_item) 
            self.update_fragrance_viewer(self.selected_id)
        else:
            self.selected_id = None
            self.update_fragrance_viewer(None)

    def delete_fragrance_record(self):
        if not self.selected_id:
            messagebox.showwarning("Warning", "Please select a fragrance to delete.")
            return

        name = get_fragrance_by_id(self.selected_id)[1]
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete fragrance: {name} (ID: {self.selected_id})? This will also delete related sales records."):
            try:
                delete_fragrance(self.selected_id)
                messagebox.showinfo("Success", "Fragrance deleted successfully.")
                self.selected_id = None
                self.update_fragrance_viewer(None)
                self.refresh_all_tables()
            except Exception as e:
                messagebox.showerror("Database Error", f"Could not delete fragrance: {e}")

    # ---------------- UI SETUP ----------------
    def load_logo(self, parent_frame):
        """Loads and displays the logo image."""
        try:
            # Check for the logo file
            if os.path.exists(LOGO_PATH):
                img = Image.open(LOGO_PATH)
                img = img.resize((50, 50), Image.Resampling.LANCZOS) # Resize logo
                self.logo_photo = ImageTk.PhotoImage(img)
                
                logo_label = ttk.Label(parent_frame, image=self.logo_photo, background=BG_LIGHT)
                logo_label.pack(side="left", padx=10, pady=5)
                
            ttk.Label(parent_frame, text="LJ Fragrances Manager", font=('Arial', 18, 'bold'), foreground=PRIMARY_ACCENT, background=BG_LIGHT).pack(side="left", padx=10, pady=10)

        except Exception as e:
            print(f"Error loading logo: {e}")
            ttk.Label(parent_frame, text="LJ Fragrances Manager", font=('Arial', 18, 'bold'), foreground=PRIMARY_ACCENT, background=BG_LIGHT).pack(side="left", padx=10, pady=10)


    def setup_ui(self):
        style = ttk.Style()
        style.theme_use("alt")  
        self.root.config(bg=BG_LIGHT)

        # 1. Base Styles
        style.configure("TFrame", background=BG_LIGHT)
        style.configure("TLabel", background=BG_LIGHT, foreground=FONT_COLOR, font=('Arial', 10))
        style.configure('Bold.TLabel', font=('Arial', 10, 'bold'))
        
        # 2. Button Styles
        style.configure("Modern.TButton", font=('Arial', 10, 'bold'), padding=[10, 5], background=BG_SECONDARY, foreground=FONT_COLOR, relief="flat", borderwidth=1, bordercolor=BORDER_COLOR)
        style.map("Modern.TButton", background=[('active', BORDER_COLOR)], foreground=[('active', PRIMARY_ACCENT)])
        style.configure("Primary.TButton", background=PRIMARY_ACCENT, foreground=BG_LIGHT, bordercolor=PRIMARY_ACCENT)
        style.map("Primary.TButton", background=[('active', '#005BB5')])

        # 3. LabelFrame Style
        style.configure("Viewer.TLabelframe", background=BG_SECONDARY, foreground=FONT_COLOR, relief="solid", borderwidth=1, font=('Arial', 11, 'bold'))
        style.configure("Viewer.TLabelframe.Label", background=BG_SECONDARY, foreground=PRIMARY_ACCENT)

        # 4. Entry/Combobox Styles
        style.configure("TEntry", padding=5, fieldbackground=BG_LIGHT, foreground=FONT_COLOR, bordercolor=BORDER_COLOR, relief="solid", borderwidth=1, insertcolor=PRIMARY_ACCENT)
        style.configure("TCombobox", padding=5, fieldbackground=BG_LIGHT, foreground=FONT_COLOR, selectforeground=FONT_COLOR, selectbackground=BG_LIGHT, bordercolor=BORDER_COLOR, relief="solid", borderwidth=1)

        # 5. Notebook/Tab Styles
        style.configure("TNotebook", background=BG_LIGHT, borderwidth=0)
        style.configure("TNotebook.Tab", padding=[15, 8], background=BG_SECONDARY, foreground=FONT_COLOR, font=('Arial', 10, 'bold'))
        style.map("TNotebook.Tab", background=[('selected', PRIMARY_ACCENT)], foreground=[('selected', BG_LIGHT)])

        # 6. Treeview Styles
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'), background=PRIMARY_ACCENT, foreground=BG_LIGHT, relief="flat", padding=[5, 8])
        style.configure("Treeview", background=BG_LIGHT, foreground=FONT_COLOR, fieldbackground=BG_LIGHT, font=('Arial', 10), rowheight=25, borderwidth=1, relief="solid")
        style.map("Treeview", background=[('selected', PRIMARY_ACCENT)], foreground=[('selected', BG_LIGHT)])


        # --- LAYOUT WIDGETS ---
        main_frame = ttk.Frame(self.root)
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # Top Frame: Logo, Search, and Image/Detail Viewer
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="x", pady=5)
        
        # --- NEW: Left Panel (for Logo and Search) ---
        left_panel = ttk.Frame(top_frame)
        left_panel.pack(side="left", fill="y", padx=5, anchor="n")

        # LOGO PLACEMENT (inside left_panel)
        logo_frame = ttk.Frame(left_panel)
        logo_frame.pack(fill="x", anchor="w")
        self.load_logo(logo_frame)
        
        # Search (inside left_panel, below logo_frame)
        search_container = ttk.Frame(left_panel)
        search_container.pack(fill="x", anchor="w", pady=(10, 0))

        search_frame = ttk.Frame(search_container)
        search_frame.pack(side="top", anchor="w")

        ttk.Label(search_frame, text="🔍 Search Fragrance:", style='Bold.TLabel').pack(side="left", padx=5)
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side="left", padx=5)
        ttk.Button(search_frame, text="Search", command=self.search_fragrance, style='Modern.TButton').pack(side="left", padx=5)
        ttk.Button(search_frame, text="Clear", command=self.refresh_all_tables, style='Modern.TButton').pack(side="left", padx=5)

        # RIGHT SIDE: Image Viewer (Stays the same, but packs next to left_panel)
        self.image_viewer_frame = ttk.LabelFrame(top_frame, text="Fragrance Details", padding="10", style='Viewer.TLabelframe')
        self.image_viewer_frame.pack(side="right", fill="y", padx=20, anchor="n")
        
        self.image_label = ttk.Label(self.image_viewer_frame, anchor="center", background=BG_SECONDARY, borderwidth=1, relief="solid")
        self.image_label.grid(row=0, column=0, padx=5, pady=5)
        
        self.detail_text_label = tk.Label(self.image_viewer_frame, justify=tk.LEFT, text="Select a fragrance to view details.", width=35, anchor="nw", background=BG_SECONDARY, fg=FONT_COLOR, font=('Arial', 10))
        self.detail_text_label.grid(row=0, column=1, padx=10, pady=5, sticky="nsw")

        # Tab Control (Notebook)
        self.tabControl = ttk.Notebook(main_frame)
        self.tabControl.pack(expand=1, fill="both", pady=10)

        # Tabs
        self.men_tab = ttk.Frame(self.tabControl)
        self.women_tab = ttk.Frame(self.tabControl)
        self.unisex_tab = ttk.Frame(self.tabControl)
        self.customer_tab = ttk.Frame(self.tabControl)
        self.sales_tab = ttk.Frame(self.tabControl)
        self.supplies_tab = ttk.Frame(self.tabControl) # Corrected typo: self.suppDlies_tab -> self.supplies_tab
        self.oils_tab = ttk.Frame(self.tabControl)
        self.expenses_tab = ttk.Frame(self.tabControl)
        self.chart_tab = ttk.Frame(self.tabControl)
        
        self.tabControl.add(self.men_tab, text="Men")
        self.tabControl.add(self.women_tab, text="Women")
        self.tabControl.add(self.unisex_tab, text="Unisex")
        self.tabControl.add(self.customer_tab, text="Customers")
        self.tabControl.add(self.sales_tab, text="Sales")
        self.tabControl.add(self.supplies_tab, text="Supplies") # Corrected typo in the call
        self.tabControl.add(self.oils_tab, text="Oils")
        self.tabControl.add(self.expenses_tab, text="Expenses")
        self.tabControl.add(self.chart_tab, text="Profit Chart")
        
        self.setup_fragrance_tab(self.men_tab, "Men")
        self.setup_fragrance_tab(self.women_tab, "Women")
        self.setup_fragrance_tab(self.unisex_tab, "Unisex")
        self.setup_customer_tab(self.customer_tab) 
        self.setup_sales_tab(self.sales_tab)
        self.setup_supplies_tab(self.supplies_tab)
        self.setup_oils_tab(self.oils_tab)
        self.setup_expenses_tab(self.expenses_tab)
        self.setup_chart_tab(self.chart_tab)
        
        # Bind tab change event
        self.tabControl.bind("<<NotebookTabChanged>>", self.on_tab_change)

    # --- *** FIXED TAB CHANGE LOGIC *** ---
# --- *** FIXED TAB CHANGE LOGIC (V2) *** ---
    # --- *** FIXED TAB CHANGE LOGIC (V3) *** ---
    def on_tab_change(self, event):
        """
        Refreshes content for the selected tab.
        Keeps fragrance viewer visible but resets functional selection for smooth re-selection.
        """
        selected_tab_text = self.tabControl.tab(self.tabControl.select(), "text")
        
        # 1. CRITICAL: Clear the *visual* selection from all fragrance trees.
        # This forces the <<TreeviewSelect>> event to fire on the next click.
        if self.men_tree:
            self.men_tree.selection_set("") 
        if self.women_tree:
            self.women_tree.selection_set("")
        if self.unisex_tree:
            self.unisex_tree.selection_set("")

        # 2. Clear the *functional* selection ID when leaving a fragrance tab group.
        # We DO NOT clear the viewer (self.update_fragrance_viewer(None)) so details persist.
        self.selected_id = None
        
        # 3. Handle specific refreshes for the *newly selected* tab
        if selected_tab_text == "Profit Chart":
            self.plot_profit_chart()
        elif selected_tab_text == "Expenses":
            self.populate_expenses()
        elif selected_tab_text == "Sales":
            self.populate_sales()
        elif selected_tab_text == "Customers":
            self.populate_customers()
        elif selected_tab_text == "Supplies":
            self.populate_supplies()
        elif selected_tab_text == "Oils":
            self.populate_oils()
        elif selected_tab_text == "Men":
             self.populate_table(self.men_tree, "Men")
        elif selected_tab_text == "Women":
             self.populate_table(self.women_tree, "Women")
        elif selected_tab_text == "Unisex":
             self.populate_table(self.unisex_tree, "Unisex")


    # ---------------- FRAGRANCE TAB SETUP (FIXED TAG_CONFIGURE) ----------------
    def setup_fragrance_tab(self, parent, gender):
        # 1. Container for Table
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)

        columns = ("ID", "Name", "Gender", "Category", "Unit Cost", "Sale Price", "Inspired By", "Quantity")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        
        # --- FIX IMPLEMENTED: Define the custom tag directly on the Treeview widget ---
        tree.tag_configure('low_stock', background=LOW_STOCK_COLOR, foreground=BG_LIGHT)
        # -----------------------------------------------------------------------------
        
        # Define column widths
        tree.column("ID", width=40, anchor="center")
        tree.column("Name", width=250)
        tree.column("Gender", width=80, anchor="center")
        tree.column("Category", width=120)
        tree.column("Unit Cost", width=80, anchor="center")
        tree.column("Sale Price", width=80, anchor="center")
        tree.column("Inspired By", width=200)
        tree.column("Quantity", width=80, anchor="center")

        for col in columns:
            tree.heading(col, text=col)
        
        tree.pack(side="left", fill="both", expand=True)
        
        # Assign to self for later use
        if gender == "Men":
            self.men_tree = tree
        elif gender == "Women":
            self.women_tree = tree
        elif gender == "Unisex":
            self.unisex_tree = tree
            
        tree.bind("<<TreeviewSelect>>", self.on_fragrance_select)

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # 2. Button Frame
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(btn_frame, text="➕ Add Fragrance", command=lambda: self.open_fragrance_form(edit=False), style='Primary.TButton').pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✏️ Edit Selected", command=lambda: self.open_fragrance_form(edit=True), style='Modern.TButton').pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ Delete Selected", command=self.delete_fragrance_record, style='Modern.TButton').pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🛒 Record Sale", command=self.record_sale, style='Modern.TButton').pack(side="right", padx=5)
        ttk.Button(btn_frame, text="🔄 Refresh", command=self.refresh_all_tables, style='Modern.TButton').pack(side="right", padx=5)
        
        self.populate_table(tree, gender)

    def search_fragrance(self):
        """Filters all fragrance treeviews based on the search entry content."""
        search_term = self.search_entry.get().strip().lower()
        
        # Function to filter and populate a single treeview
        def filter_tree(tree, gender):
            if tree:
                for row in tree.get_children():
                    tree.delete(row)
            else:
                return 
            
            fragrances = get_all_fragrances_by_gender(gender)
            
            if search_term:
                filtered_fragrances = []
                for f in fragrances:
                    # f is a tuple: (id, name, desc, gender, cat, u_cost, s_price, inspired, qty, img_path)
                    name = str(f[1] or "").lower()
                    desc = str(f[2] or "").lower()
                    
                    if search_term in name or search_term in desc:
                        filtered_fragrances.append(f)
            else:
                filtered_fragrances = fragrances 

            for i, f in enumerate(filtered_fragrances):
                tags = ()
                quantity = int(f[8] or 0)
                if quantity <= 5: 
                    tags = ('low_stock',)
                    
                tree.insert("", "end", iid=str(f[0]), tags=tags, 
                                values=(f[0], f[1], f[3], f[4], f"{f[5]:.2f}", f"{f[6]:.2f}", f[7], quantity))

        filter_tree(self.men_tree, "Men")
        filter_tree(self.women_tree, "Women")
        filter_tree(self.unisex_tree, "Unisex")
        
        self.update_fragrance_viewer(None)

    def choose_image(self, entry_widget):
        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files","*.png *.jpg *.jpeg *.gif *.bmp"),("All files","*.*")]
        )
        if path:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, path)

    def open_fragrance_form(self, edit=False):
        f_data = get_fragrance_by_id(self.selected_id) if edit and self.selected_id else None
        
        if edit and not f_data:
             messagebox.showerror("Error", "No fragrance selected or found.")
             return

        form = tk.Toplevel(self.root)
        form.title("Edit Fragrance" if edit else "Add Fragrance")
        form.geometry("450x450")
        form.config(bg=BG_LIGHT)
        form_frame = ttk.Frame(form, padding=10)
        form_frame.pack(fill="both", expand=True)

        fields = ["Name", "Description", "Gender", "Category", "Unit Cost", "Sale Price", "Inspired By", "Quantity", "Image"]
        entries = {}

        for i, field in enumerate(fields):
            ttk.Label(form_frame, text=f"{field}:").grid(row=i, column=0, padx=5, pady=5, sticky="w")
            
            if field == "Gender":
                entry = ttk.Combobox(form_frame, values=["Men", "Women", "Unisex"], state="readonly", style='TCombobox')
            else:
                entry = ttk.Entry(form_frame, style='TEntry')
            
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            # Indexing f_data: f_data is a tuple from DB: (id, name, desc, gender, cat, u_cost, s_price, inspired, qty, img_path)
            if edit and f_data and i < 9: # We skip ID (index 0) in the form
                db_index = i + 1
                value = f_data[db_index] if db_index < len(f_data) and f_data[db_index] is not None else ""
                
                # Format numeric fields for display
                if field in ["Unit Cost", "Sale Price"]:
                    try:
                        value = f"{float(value):.2f}"
                    except (ValueError, TypeError):
                        value = "0.00"
                elif field == "Quantity":
                    try:
                        value = str(int(value))
                    except (ValueError, TypeError):
                        value = "0"

                entry.insert(0, value)
            entries[field] = entry

        ttk.Button(form_frame, text="Choose Image", command=lambda: self.choose_image(entries["Image"]), style='Modern.TButton').grid(row=8, column=2, padx=5)

        # --- COMPLETED SAVE FUNCTION ---
        def save():
            name = entries["Name"].get().strip()
            desc = entries["Description"].get().strip()
            gender = entries["Gender"].get().strip()
            category = entries["Category"].get().strip()
            inspired_by = entries["Inspired By"].get().strip()
            
            # --- VALIDATION ---
            unit_cost = self.validate_numeric_input(entries["Unit Cost"].get(), "Unit Cost", is_integer=False)
            sale_price = self.validate_numeric_input(entries["Sale Price"].get(), "Sale Price", is_integer=False)
            quantity = self.validate_numeric_input(entries["Quantity"].get(), "Quantity", is_integer=True)
            image_path = entries["Image"].get().strip()
            
            if None in (unit_cost, sale_price, quantity) or not name or not gender:
                messagebox.showerror("Input Error", "Name, Gender, and valid numbers for cost/quantity are required.")
                return

            # Fragrance data tuple (matching the DB structure, excluding ID)
            f_data = (name, desc, gender, category, unit_cost, sale_price, inspired_by, quantity, image_path)
            
            if edit and self.selected_id:
                update_fragrance(self.selected_id, f_data)
                messagebox.showinfo("Success", f"Fragrance ID {self.selected_id} updated.")
            else:
                insert_fragrance(f_data)
                messagebox.showinfo("Success", f"New fragrance '{name}' added.")
            
            self.refresh_all_tables()
            self.update_fragrance_viewer(self.selected_id if edit else None)
            form.destroy()
            
        # Add the SAVE button call back to the form frame
        ttk.Button(form_frame, text=("Save Changes" if edit else "Add Fragrance"), 
                   command=save, style='Primary.TButton').grid(row=9, column=1, pady=10, sticky="e")
        form_frame.grid_columnconfigure(1, weight=1)
        # --- END COMPLETED SAVE FUNCTION ---

    # ---------------- CUSTOMER LOGIC ----------------
    def on_customer_select(self, event):
        """Sets the selected_customer_id when a customer is selected."""
        tree = event.widget
        selected_item = tree.focus()
        if selected_item:
            # Assumes ID is the first value in the row
            self.selected_customer_id = int(tree.item(selected_item)['values'][0])
        else:
            self.selected_customer_id = None
            
    def setup_customer_tab(self, parent):
        """Sets up the UI for the Customers tab."""
        # 1. Container for Table
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)

        columns = ("ID", "Name", "Email", "Phone", "City", "Reference")
        self.customer_tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        
        self.customer_tree.column("ID", width=40, anchor="center")
        self.customer_tree.column("Name", width=180)
        self.customer_tree.column("Email", width=200)
        self.customer_tree.column("Phone", width=120)
        self.customer_tree.column("City", width=120)
        self.customer_tree.column("Reference", width=150)

        for col in columns:
            self.customer_tree.heading(col, text=col)
        
        self.customer_tree.pack(side="left", fill="both", expand=True)
        self.customer_tree.bind("<<TreeviewSelect>>", self.on_customer_select)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.customer_tree.yview)
        self.customer_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # 2. Button Frame
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(btn_frame, text="➕ Add Customer", command=lambda: self.open_customer_form(edit=False), style='Primary.TButton').pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✏️ Edit Selected", command=lambda: self.open_customer_form(edit=True), style='Modern.TButton').pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ Delete Selected", command=self.delete_customer_record, style='Modern.TButton').pack(side="left", padx=5)
        
        self.populate_customers()

    def populate_customers(self):
        """Fetches and populates the customer table."""
        if not self.customer_tree: return
        for row in self.customer_tree.get_children():
            self.customer_tree.delete(row)
            
        customers = get_all_customers()
        # Customer DB structure: (id, name, email, phone, city, reference)
        for c in customers:
            self.customer_tree.insert("", "end", iid=str(c[0]), values=c)
            
    def open_customer_form(self, edit=False):
        """Opens a form to add or edit a customer."""
        c_data = get_customer_by_id(self.selected_customer_id) if edit and self.selected_customer_id else None

        if edit and not c_data:
             messagebox.showerror("Error", "No customer selected or found.")
             return
             
        form = tk.Toplevel(self.root)
        form.title("Edit Customer" if edit else "Add Customer")
        form.geometry("400x300")
        form.config(bg=BG_LIGHT)
        form_frame = ttk.Frame(form, padding=10)
        form_frame.pack(fill="both", expand=True)

        fields = ["Name", "Email", "Phone", "City", "Reference"]
        entries = {}

        for i, field in enumerate(fields):
            ttk.Label(form_frame, text=f"{field}:").grid(row=i, column=0, padx=5, pady=5, sticky="w")
            entry = ttk.Entry(form_frame, style='TEntry')
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            
            # c_data is (id, name, email, phone, city, reference)
            if edit and c_data and i + 1 < len(c_data):
                entry.insert(0, c_data[i + 1] if c_data[i + 1] is not None else "")
            entries[field] = entry

        def save():
            data = (entries[f].get().strip() for f in fields)
            c_data = tuple(data)
            
            if not c_data[0]:
                messagebox.showerror("Input Error", "Name is required.")
                return

            if edit and self.selected_customer_id:
                update_customer(self.selected_customer_id, c_data)
                messagebox.showinfo("Success", f"Customer ID {self.selected_customer_id} updated.")
            else:
                insert_customer(c_data)
                messagebox.showinfo("Success", f"New customer '{c_data[0]}' added.")
            
            self.populate_customers()
            form.destroy()

        ttk.Button(form_frame, text=("Save Changes" if edit else "Add Customer"), 
                   command=save, style='Primary.TButton').grid(row=len(fields), column=1, pady=10, sticky="e")
        form_frame.grid_columnconfigure(1, weight=1)

    def delete_customer_record(self):
        """Deletes the selected customer record."""
        if not self.selected_customer_id:
            messagebox.showwarning("Warning", "Please select a customer to delete.")
            return

        name = get_customer_by_id(self.selected_customer_id)[1]
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete customer: {name} (ID: {self.selected_customer_id})? This will also delete related sales records."):
            try:
                delete_customer(self.selected_customer_id)
                messagebox.showinfo("Success", "Customer deleted successfully.")
                self.selected_customer_id = None
                self.populate_customers()
            except Exception as e:
                messagebox.showerror("Database Error", f"Could not delete customer: {e}")

    # ---------------- SALES LOGIC ----------------
    def record_sale(self):
        if not self.selected_id:
            messagebox.showwarning("No Selection", "Select fragrance to sell")
            return
            
        all_customers = get_all_customers()
        if not all_customers:
            messagebox.showwarning("No Customers", "No customers found. Please add a customer first.")
            return
            
        fragrance = get_fragrance_by_id(self.selected_id)
        if not fragrance:
            messagebox.showerror("Error", "Fragrance not found")
            return

        form = tk.Toplevel(self.root)
        form.title(f"Record Sale: {fragrance[1]}")
        form.geometry("400x300")
        form.config(bg=BG_LIGHT)
        form_frame = ttk.Frame(form, padding=10)
        form_frame.pack(fill="both", expand=True)

        ttk.Label(form_frame, text="Customer:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        customers = [f"{c[1]} (ID:{c[0]})" for c in all_customers]
        customer_var = tk.StringVar()
        cust_combo = ttk.Combobox(form_frame, values=customers, textvariable=customer_var, state="readonly", style='TCombobox')
        cust_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(form_frame, text="Quantity:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        qty_entry = ttk.Entry(form_frame, style='TEntry')
        qty_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(form_frame, text=f"Sale Price: ${fragrance[6]:.2f}").grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="w")


        def save_sale():
            if not customer_var.get():
                messagebox.showwarning("Error", "Select customer")
                return
            
            # --- VALIDATION INTEGRATION ---
            qty = self.validate_numeric_input(qty_entry.get(), "Quantity", is_integer=True)
            if qty is None: return
            if qty <= 0:
                messagebox.showerror("Error", "Quantity must be a positive number")
                return
            
            current_qty = int(fragrance[8] or 0)
            if qty > current_qty:
                messagebox.showerror("Error", f"Not enough stock. Available: {current_qty}")
                return
            # ------------------------------
            
            customer_id = int(customer_var.get().split("ID:")[1].replace(")", ""))
            unit_cost = float(fragrance[5])
            sale_price = float(fragrance[6])
            revenue = sale_price * qty
            profit = (sale_price - unit_cost) * qty
            date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Insert sale record
            insert_sale((self.selected_id, customer_id, qty, unit_cost, sale_price, revenue, profit, date))
            # Update fragrance stock
            update_fragrance_quantity(self.selected_id, current_qty - qty)
            
            self.populate_sales()
            self.refresh_all_tables()
            self.update_fragrance_viewer(self.selected_id)
            form.destroy()

        ttk.Button(form_frame, text="Save Sale", command=save_sale, style='Primary.TButton').grid(row=3, column=1, pady=10, sticky="e")
        form_frame.grid_columnconfigure(1, weight=1)
        
    def setup_sales_tab(self, parent):
        """Sets up the UI for the Sales tab."""
        # 1. Container for Table
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)

        columns = ("ID", "Fragrance Name", "Customer Name", "Qty Sold", "Unit Cost", "Sale Price", "Revenue", "Profit", "Date")
        self.sales_tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        
        self.sales_tree.column("ID", width=40, anchor="center")
        self.sales_tree.column("Fragrance Name", width=180)
        self.sales_tree.column("Customer Name", width=150)
        self.sales_tree.column("Qty Sold", width=80, anchor="center")
        self.sales_tree.column("Unit Cost", width=80, anchor="center")
        self.sales_tree.column("Sale Price", width=80, anchor="center")
        self.sales_tree.column("Revenue", width=100, anchor="center")
        self.sales_tree.column("Profit", width=100, anchor="center")
        self.sales_tree.column("Date", width=150, anchor="center")

        for col in columns:
            self.sales_tree.heading(col, text=col)
        
        self.sales_tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.sales_tree.yview)
        self.sales_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # 2. Controls Frame
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill="x", pady=5)
        
        ttk.Label(controls_frame, text="Filter by Month:", style='Bold.TLabel').pack(side="left", padx=5)
        
        self.sales_month_combo = ttk.Combobox(controls_frame, textvariable=self.sales_month_var, state="readonly", width=15, style='TCombobox')
        self.sales_month_combo.pack(side="left", padx=5)
        self.sales_month_combo.bind("<<ComboboxSelected>>", self.populate_sales)
        
        ttk.Button(controls_frame, text="🔄 Refresh", command=self.populate_sales, style='Modern.TButton').pack(side="right", padx=5)
        
        self.populate_sales()

    def populate_sales(self, event=None):
        """Fetches and populates the sales table, optionally filtered by month."""
        if not self.sales_tree: return
        for row in self.sales_tree.get_children():
            self.sales_tree.delete(row)
            
        # Get all sales to determine months
        all_sales = get_all_sales()
        
        # 1. Update Month ComboBox
        months = sorted(list(set([s[8][:7] for s in all_sales if s[8]])), reverse=True)
        months.insert(0, "All Months")
        if self.sales_month_combo:
            current_month_selection = self.sales_month_var.get()
            self.sales_month_combo['values'] = months
            if current_month_selection not in months:
                self.sales_month_var.set("All Months")
                
        selected_month_year = self.sales_month_var.get()
        
        if selected_month_year == "All Months":
            sales = all_sales
        else:
            try:
                year, month = map(int, selected_month_year.split('-'))
                sales = get_sales_by_month(month, year)
            except ValueError:
                sales = [] # Handle invalid format if somehow set

        # Sales DB structure: (s.id, f.name, c.name, s.qty_sold, s.unit_cost, s.sale_price, s.revenue, s.profit, s.date)
        for s in sales:
            # Format currency values
            formatted_values = (
                s[0], s[1] or "Unknown Fragrance", s[2] or "Unknown Customer", s[3],
                f"{s[4]:.2f}", f"{s[5]:.2f}", f"{s[6]:.2f}", f"{s[7]:.2f}", s[8]
            )
            self.sales_tree.insert("", "end", values=formatted_values)

    # ---------------- SUPPLIES LOGIC ----------------
    def on_supply_select(self, event):
        tree = event.widget
        selected_item = tree.focus()
        self.selected_supply_id = int(tree.item(selected_item)['values'][0]) if selected_item else None

    def setup_supplies_tab(self, parent):
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)
        columns = ("ID", "Name", "Price", "Purchase Link", "Quantity")
        self.supplies_tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        
        self.supplies_tree.column("ID", width=40, anchor="center")
        self.supplies_tree.column("Name", width=250)
        self.supplies_tree.column("Price", width=100, anchor="center")
        self.supplies_tree.column("Purchase Link", width=300)
        self.supplies_tree.column("Quantity", width=80, anchor="center")
        for col in columns: self.supplies_tree.heading(col, text=col)
        self.supplies_tree.pack(side="left", fill="both", expand=True)
        self.supplies_tree.bind("<<TreeviewSelect>>", self.on_supply_select)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.supplies_tree.yview)
        self.supplies_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="➕ Add Supply", command=lambda: self.open_supply_form(edit=False), style='Primary.TButton').pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✏️ Edit Selected", command=lambda: self.open_supply_form(edit=True), style='Modern.TButton').pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ Delete Selected", command=self.delete_supply_record, style='Modern.TButton').pack(side="left", padx=5)
        self.populate_supplies()

    def populate_supplies(self):
        if not self.supplies_tree: return
        for row in self.supplies_tree.get_children(): self.supplies_tree.delete(row)
        supplies = get_all_supplies()
        # Supply DB structure: (id, name, price, purchase_link, quantity)
        for s in supplies:
            self.supplies_tree.insert("", "end", values=(s[0], s[1], f"{s[2]:.2f}", s[3], s[4]))
            
    def open_supply_form(self, edit=False):
        s_data = get_supply_by_id(self.selected_supply_id) if edit and self.selected_supply_id else None
        
        if edit and not s_data:
             messagebox.showerror("Error", "No supply selected or found.")
             return
             
        form = tk.Toplevel(self.root); form.title("Edit Supply" if edit else "Add Supply"); form.geometry("400x300")
        form.config(bg=BG_LIGHT); form_frame = ttk.Frame(form, padding=10); form_frame.pack(fill="both", expand=True)

        fields = ["Name", "Price", "Purchase Link", "Quantity"]
        entries = {}
        for i, field in enumerate(fields):
            ttk.Label(form_frame, text=f"{field}:").grid(row=i, column=0, padx=5, pady=5, sticky="w")
            entry = ttk.Entry(form_frame, style='TEntry'); entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            # s_data is (id, name, price, purchase_link, quantity)
            if edit and s_data and i + 1 < len(s_data):
                value = f"{s_data[i+1]:.2f}" if field == "Price" else str(s_data[i+1])
                entry.insert(0, value.replace("$", "") if value else "")
            entries[field] = entry

        def save():
            name = entries["Name"].get().strip(); link = entries["Purchase Link"].get().strip()
            price = self.validate_numeric_input(entries["Price"].get(), "Price", is_integer=False)
            qty = self.validate_numeric_input(entries["Quantity"].get(), "Quantity", is_integer=True)
            if None in (price, qty) or not name:
                messagebox.showerror("Input Error", "Name and valid numbers for price/quantity are required.")
                return

            s_data = (name, price, link, qty)
            if edit and self.selected_supply_id:
                update_supply(self.selected_supply_id, s_data); messagebox.showinfo("Success", "Supply updated.")
            else:
                insert_supply(s_data); messagebox.showinfo("Success", "New supply added.")
            
            self.populate_supplies(); form.destroy()

        ttk.Button(form_frame, text=("Save Changes" if edit else "Add Supply"), command=save, style='Primary.TButton').grid(row=len(fields), column=1, pady=10, sticky="e")
        form_frame.grid_columnconfigure(1, weight=1)

    def delete_supply_record(self):
        if not self.selected_supply_id:
            messagebox.showwarning("Warning", "Select a supply to delete.")
            return
        name = get_supply_by_id(self.selected_supply_id)[1]
        if messagebox.askyesno("Confirm Delete", f"Delete supply: {name}?"):
            delete_supply(self.selected_supply_id)
            messagebox.showinfo("Success", "Supply deleted.")
            self.selected_supply_id = None; self.populate_supplies()

    # ---------------- OILS LOGIC ----------------
    def on_oil_select(self, event):
        tree = event.widget
        selected_item = tree.focus()
        self.selected_oil_id = int(tree.item(selected_item)['values'][0]) if selected_item else None

    def setup_oils_tab(self, parent):
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)
        columns = ("ID", "Name", "Size (ml)", "Price", "Purchase Link", "Quantity")
        self.oils_tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        
        self.oils_tree.column("ID", width=40, anchor="center")
        self.oils_tree.column("Name", width=250)
        self.oils_tree.column("Size (ml)", width=100, anchor="center")
        self.oils_tree.column("Price", width=100, anchor="center")
        self.oils_tree.column("Purchase Link", width=300)
        self.oils_tree.column("Quantity", width=80, anchor="center")
        for col in columns: self.oils_tree.heading(col, text=col)
        self.oils_tree.pack(side="left", fill="both", expand=True)
        self.oils_tree.bind("<<TreeviewSelect>>", self.on_oil_select)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.oils_tree.yview)
        self.oils_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="➕ Add Oil", command=lambda: self.open_oil_form(edit=False), style='Primary.TButton').pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✏️ Edit Selected", command=lambda: self.open_oil_form(edit=True), style='Modern.TButton').pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ Delete Selected", command=self.delete_oil_record, style='Modern.TButton').pack(side="left", padx=5)
        self.populate_oils()

    def populate_oils(self):
        if not self.oils_tree: return
        for row in self.oils_tree.get_children(): self.oils_tree.delete(row)
        oils = get_all_oils()

        # FIX: Helper function to safely format numeric data that might be None
        def safe_float_format(value):
            if value is None or str(value).strip() == '':
                return "0.00"
            try:
                return f"{float(value):.2f}"
            except (ValueError, TypeError):
                return "0.00"
        
        # Oils DB structure: (id, name, size, price, purchase_link, quantity)
        for o in oils:
            # Safely format size (o[2]) and price (o[3])
            size_formatted = safe_float_format(o[2])
            price_formatted = safe_float_format(o[3])
            
            self.oils_tree.insert("", "end", 
                                 values=(o[0], o[1], size_formatted, price_formatted, o[4], o[5]))
            
    def open_oil_form(self, edit=False):
        o_data = get_oil_by_id(self.selected_oil_id) if edit and self.selected_oil_id else None
        
        if edit and not o_data:
             messagebox.showerror("Error", "No oil selected or found.")
             return
             
        form = tk.Toplevel(self.root); form.title("Edit Oil" if edit else "Add Oil"); form.geometry("400x300")
        form.config(bg=BG_LIGHT); form_frame = ttk.Frame(form, padding=10); form_frame.pack(fill="both", expand=True)

        fields = ["Name", "Size (ml)", "Price", "Purchase Link", "Quantity"]
        entries = {}
        for i, field in enumerate(fields):
            ttk.Label(form_frame, text=f"{field}:").grid(row=i, column=0, padx=5, pady=5, sticky="w")
            entry = ttk.Entry(form_frame, style='TEntry'); entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            # o_data is (id, name, size, price, purchase_link, quantity)
            if edit and o_data and i + 1 < len(o_data):
                value = str(o_data[i+1])
                if field in ["Size (ml)", "Price"]:
                    try: value = f"{float(value):.2f}"
                    except: pass
                entry.insert(0, value.replace("$", "") if value else "")
            entries[field] = entry

        def save():
            name = entries["Name"].get().strip(); link = entries["Purchase Link"].get().strip()
            size = self.validate_numeric_input(entries["Size (ml)"].get(), "Size", is_integer=False)
            price = self.validate_numeric_input(entries["Price"].get(), "Price", is_integer=False)
            qty = self.validate_numeric_input(entries["Quantity"].get(), "Quantity", is_integer=True)
            if None in (size, price, qty) or not name:
                messagebox.showerror("Input Error", "Name and valid numbers for size/price/quantity are required.")
                return

            o_data = (name, size, price, link, qty)
            if edit and self.selected_oil_id:
                update_oil(self.selected_oil_id, o_data); messagebox.showinfo("Success", "Oil updated.")
            else:
                insert_oil(o_data); messagebox.showinfo("Success", "New oil added.")
            
            self.populate_oils(); form.destroy()

        ttk.Button(form_frame, text=("Save Changes" if edit else "Add Oil"), command=save, style='Primary.TButton').grid(row=len(fields), column=1, pady=10, sticky="e")
        form_frame.grid_columnconfigure(1, weight=1)

    def delete_oil_record(self):
        if not self.selected_oil_id:
            messagebox.showwarning("Warning", "Select an oil to delete.")
            return
        name = get_oil_by_id(self.selected_oil_id)[1]
        if messagebox.askyesno("Confirm Delete", f"Delete oil: {name}?"):
            delete_oil(self.selected_oil_id)
            messagebox.showinfo("Success", "Oil deleted.")
            self.selected_oil_id = None; self.populate_oils()

    # ---------------- EXPENSE TAB SETUP AND LOGIC (MODIFIED) ----------------
    def setup_expenses_tab(self, parent):
        # Top Frame for Monthly Summary and Add Button
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill="x", padx=5, pady=5)
        
        # Monthly Total Display and Filter
        summary_frame = ttk.LabelFrame(top_frame, text="Monthly Summary", padding=10, style='Viewer.TLabelframe')
        summary_frame.pack(side="left", padx=10)
        
        self.month_var.set("All Months") # Reset variable
        
        self.month_combo = ttk.Combobox(summary_frame, textvariable=self.month_var, state="readonly", width=15, style='TCombobox')
        self.month_combo.pack(side="left", padx=5)
        self.month_combo.bind("<<ComboboxSelected>>", self.populate_expenses)
        
        self.total_expense_label = ttk.Label(summary_frame, text="Total Expenses: $0.00", style='Bold.TLabel', background=BG_SECONDARY)
        self.total_expense_label.pack(side="left", padx=15)
        
        # Add Expense Button
        btn_frame = ttk.Frame(top_frame)
        btn_frame.pack(side="right", padx=5)
        ttk.Button(btn_frame, text="➕ Record Expense", command=self.open_expense_form, style='Primary.TButton').pack(side="right", padx=5)

        # Table Frame
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # --- MODIFIED Columns to match new schema ---
        columns = ("ID", "Date", "Item Name", "Cost", "Quantity", "Supplier", "Total Cost")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        tree.column("ID", width=40, anchor="center")
        tree.column("Date", width=150, anchor="center")
        tree.column("Item Name", width=250)
        tree.column("Cost", width=100, anchor="center")
        tree.column("Quantity", width=80, anchor="center")
        tree.column("Supplier", width=200)
        tree.column("Total Cost", width=120, anchor="center")

        for col in columns:
            tree.heading(col, text=col)
        
        tree.pack(side="left", fill="both", expand=True)
        self.expenses_tree = tree
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        self.populate_expenses() # Initial population

    # --- MODIFIED Expense Form ---
    def open_expense_form(self):
        form = tk.Toplevel(self.root)
        form.title("Record New Expense")
        form.geometry("450x300")
        form.config(bg=BG_LIGHT)
        form_frame = ttk.Frame(form, padding=15)
        form_frame.pack(fill="both", expand=True)

        fields = ["Item Name", "Cost (per item)", "Quantity", "Supplier (Optional)"]
        entries = {}

        for i, field in enumerate(fields):
            ttk.Label(form_frame, text=f"{field}:").grid(row=i, column=0, padx=5, pady=5, sticky="w")
            entry = ttk.Entry(form_frame, style='TEntry')
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            entries[field] = entry
            
        def save():
            item_name = entries["Item Name"].get().strip()
            supplier = entries["Supplier (Optional)"].get().strip()
            
            # 1. Basic Required Field Check
            if not item_name:
                messagebox.showerror("Input Error", "Item Name is required.")
                return

            # 2. Numeric Validation
            cost = self.validate_numeric_input(entries["Cost (per item)"].get(), "Cost", is_integer=False)
            quantity = self.validate_numeric_input(entries["Quantity"].get(), "Quantity", is_integer=True)
            
            if cost is None or quantity is None:
                return # Validation function already showed error

            if cost <= 0 or quantity <= 0:
                messagebox.showerror("Input Error", "Cost and Quantity must be greater than zero.")
                return

            # 3. Final Calculation and Save
            total_cost = cost * quantity
            expense_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # DB structure: (item_name, cost, quantity, supplier, total_cost, date)
            insert_expense((item_name, cost, quantity, supplier, total_cost, expense_date))
            
            messagebox.showinfo("Success", "Expense recorded.")
            self.populate_expenses()
            form.destroy()

        ttk.Button(form_frame, text="Save Expense", command=save, style='Primary.TButton').grid(row=len(fields), column=1, pady=15, sticky="e")
        form_frame.grid_columnconfigure(1, weight=1)

    # --- MODIFIED to populate new table structure ---
    def populate_expenses(self, event=None):
        if not self.expenses_tree: return
        for row in self.expenses_tree.get_children():
            self.expenses_tree.delete(row)

        all_expenses = get_all_expenses()
        
        # Expense DB structure: (id, item_name, cost, quantity, supplier, total_cost, date)
        
        # 1. Update Month ComboBox
        months = sorted(list(set([e[6] for e in all_expenses if e[6]])), key=lambda x: x[:7], reverse=True)
        # Get unique YYYY-MM
        unique_months = sorted(list(set([m[:7] for m in months])), reverse=True)
        unique_months.insert(0, "All Months")
        
        if self.month_combo:
            current_month_selection = self.month_var.get()
            self.month_combo['values'] = unique_months
            if current_month_selection not in unique_months:
                self.month_var.set("All Months")
        
        selected_month = self.month_var.get()
        
        monthly_total = 0.0
        
        for e in all_expenses:
            # e: (id, item_name, cost, quantity, supplier, total_cost, date)
            date_str = e[6]
            
            # 2. Filtering by Month
            if selected_month != "All Months" and (not date_str or not date_str.startswith(selected_month)):
                continue
                
            try:
                total_cost_float = float(e[5]) # Index 5 is total_cost
            except (TypeError, ValueError):
                total_cost_float = 0.0

            monthly_total += total_cost_float
            
            # 3. Insert into Treeview
            self.expenses_tree.insert("", "end", iid=str(e[0]), 
                values=(
                    str(e[0]), # id
                    e[6],       # date
                    e[1],       # item_name
                    f"{e[2]:.2f}", # cost
                    e[3],       # quantity
                    e[4],       # supplier
                    f"{e[5]:.2f}"  # total_cost
                )
            )

        # 4. Update Summary Label
        if self.total_expense_label:
            display_month = selected_month.replace('-', '/') if selected_month != "All Months" else selected_month
            self.total_expense_label.config(text=f"Total Expenses ({display_month}): ${monthly_total:.2f}")

    # ---------------- PROFIT CHART TAB SETUP AND LOGIC (MODIFIED) ----------------
    def setup_chart_tab(self, parent):
        self.chart_frame = ttk.Frame(parent)
        self.chart_frame.pack(fill="both", expand=True)
        # Placeholder for initial plot
        self.plot_profit_chart() 

    def plot_profit_chart(self):
        # Clear previous chart if exists
        if self.chart_canvas_container:
            self.chart_canvas_container.get_tk_widget().destroy()
            self.chart_canvas_container = None
        
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        # 1. Get Monthly Data (Sales and Expenses)
        
        all_sales = get_all_sales()
        all_expenses = get_all_expenses()
        
        expense_data = {}
        # Expense DB structure: (id, item_name, cost, quantity, supplier, total_cost, date)
        for e in all_expenses:
            date_str = e[6] # --- FIXED: Index 6 is the date column
            if date_str:
                month_key = date_str[:7]
                try:
                    total_cost = float(e[5]) # --- FIXED: Index 5 is the total_cost
                except (ValueError, TypeError):
                    total_cost = 0.0

                expense_data[month_key] = expense_data.get(month_key, 0.0) + total_cost

        # 2. Consolidate Data (Calculating Monthly Sales Totals)
        sales_totals = {}
        # sales: (s.id, f.name, c.name, s.qty_sold, s.unit_cost, s.sale_price, s.revenue, s.profit, s.date)
        for sale in all_sales:
            date_str = sale[8] # Index 8 is the date column
            if date_str:
                month_key = date_str[:7]
                revenue = float(sale[6])
                # COGS (Cost of Goods Sold) = unit_cost * qty_sold
                cogs = float(sale[4]) * float(sale[3]) 
                
                if month_key not in sales_totals:
                    sales_totals[month_key] = {'revenue': 0.0, 'cogs': 0.0}
                
                sales_totals[month_key]['revenue'] += revenue
                sales_totals[month_key]['cogs'] += cogs
                
        all_months = sorted(list(set(sales_totals.keys()) | set(expense_data.keys())))
        
        if not all_months:
            ttk.Label(self.chart_frame, text="No sales or expense data available to plot.", font=('Arial', 12, 'italic')).pack(pady=50)
            return

        revenue = [sales_totals.get(m, {'revenue': 0.0})['revenue'] for m in all_months]
        sales_cogs = [sales_totals.get(m, {'cogs': 0.0})['cogs'] for m in all_months]
        
        # Total operating cost (COGS + general overhead expenses)
        general_expenses = [expense_data.get(m, 0.0) for m in all_months]
        total_expense = [sales_cogs[i] + general_expenses[i] for i in range(len(all_months))]
        
        profit = [revenue[i] - total_expense[i] for i in range(len(all_months))]

        # 3. Plotting with Matplotlib
        fig, ax1 = plt.subplots(figsize=(10, 5))
        
        # Bar Chart for Revenue and Total Expense
        width = 0.35
        x = range(len(all_months))
        
        ax1.bar([i - width/2 for i in x], revenue, width, label='Total Revenue', color=PRIMARY_ACCENT)
        ax1.bar([i + width/2 for i in x], total_expense, width, label='Total Expenses', color=LOW_STOCK_COLOR)
        
        ax1.set_xlabel("Month (YYYY-MM)")
        ax1.set_ylabel("Amount ($)", color=FONT_COLOR)
        ax1.tick_params(axis='y', labelcolor=FONT_COLOR)
        ax1.set_xticks(x)
        ax1.set_xticklabels(all_months, rotation=45, ha="right")
        ax1.legend(loc='upper left')

        # Line for Profit (Secondary Axis)
        ax2 = ax1.twinx()
        ax2.plot(x, profit, color='#4CAF50', marker='o', linestyle='-', linewidth=2, label='Net Profit')
        ax2.set_ylabel("Net Profit ($)", color='#4CAF50')
        ax2.tick_params(axis='y', labelcolor='#4CAF50')
        ax2.legend(loc='upper right')

        fig.tight_layout()
        
        # 4. Embed into Tkinter
        self.chart_canvas_container = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.chart_canvas_container.draw()
        self.chart_canvas_container.get_tk_widget().pack(fill=tk.BOTH, expand=1)

# ---------------- MAIN EXECUTION ----------------
if __name__ == "__main__":
    root = tk.Tk()
    app = FragranceManagerApp(root)
    root.mainloop()