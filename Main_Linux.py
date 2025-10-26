import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime # Used for date handling in sales and expense logic
import numpy as np # Added for chart bar positioning
# Assuming you saved the scanner logic in a file named qr_scanner.py
try:
    from qr_scanner import scan_qr_code
except ImportError:
    # If the file or libraries aren't present, disable the feature gracefully
    print("Warning: qr_scanner.py or required libraries (opencv-python, pyzbar) not found. QR Scan feature will be disabled.")
    scan_qr_code = None
#pip install opencv-python pyzbar
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
    
    # REPORTING
    get_monthly_summary_data
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
        self.fragrances_tree = None # Replaces men_tree, women_tree, unisex_tree
        self.fragrances_search_entry = None # For in-tab search
        self.fragrances_gender_filter = None # For in-tab filter
        self.customer_tree = None
        self.sales_tree = None
        self.supplies_tree = None
        self.oils_tree = None
        self.expenses_tree = None
        
        # Chart & Summary UI References
        self.graph_frame = None # Frame to hold the chart canvas
        self.chart_month_selector = None
        self.summary_revenue_label = None
        self.summary_cogs_label = None
        self.summary_overhead_label = None
        self.summary_profit_label = None
        self.summary_total_stock_label = None
        self.summary_total_value_label = None
        self.summary_retail_value_label = None # NEW: Retail Value Label
        
        # StringVars for filters
        self.expense_month_var = tk.StringVar(value="All Months") 
        self.sales_month_var = tk.StringVar(value="All Months")
        self.total_expense_label = None 
        self.expense_month_filter = None 

        init_db() # This will now run the migration
        
        # Ensure image directory exists
        if not os.path.exists(IMAGE_DIR):
            os.makedirs(IMAGE_DIR)

        self.setup_ui()
        self.refresh_all_tables() # Initial population
    def copy_oil_link(self, event):
        """Copies the purchase link of the double-clicked oil record to the clipboard."""
        try:
            # Identify the item and column that was double-clicked
            item_id = self.oils_tree.identify_row(event.y)
            column_id = self.oils_tree.identify_column(event.x)
            
            # Check if an item was selected and if it's the 'Purchase Link' column
            # The column indices start at #1 for the first *visible* column (which is 'ID' here).
            # If 'Purchase Link' is the 5th visible column (ID, Name, Size, Price, Link),
            # its identifier will be #5. Let's confirm the column index.
            # Columns in setup_oils_tab: ("ID", "Name", "Size (ml)", "Price", "Purchase Link", "Quantity")
            # Index for 'Purchase Link' is 4 (zero-indexed list of column names, but Treeview columns are #1, #2, #3, #4, #5, #6)
            
            if item_id and column_id == '#5': # Assuming Purchase Link is the 5th column (#5)
                # Get the values for the selected item
                values = self.oils_tree.item(item_id, 'values')
                
                # 'Purchase Link' is at index 4 (0-based) in the values tuple
                purchase_link = values[4]
                
                if purchase_link:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(purchase_link)
                    self.root.update() # Update the clipboard
                    messagebox.showinfo("Copied", f"Link copied to clipboard:\n{purchase_link[:60]}...")
                else:
                    messagebox.showwarning("No Link", "The selected oil does not have a purchase link.")
            
        except IndexError:
            # Happens if the user clicks outside of a data cell
            pass
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy link: {e}")
    def scan_and_search_fragrance(self):
        """Calls the QR scanner and uses the returned ID to search the table."""
        if scan_qr_code is None:
            messagebox.showerror("Feature Disabled", "The QR Scanning feature is disabled because the required libraries (opencv-python, pyzbar) or scanner file are missing.")
            return

        # Pass self.root to keep the scanner window on top
        fragrance_id = scan_qr_code(self.root) 

        if fragrance_id is not None:
            # Convert ID to string for entry box
            id_str = str(fragrance_id)
            
            # 1. Update the search entry box with the found ID
            self.fragrances_search_entry.delete(0, tk.END)
            self.fragrances_search_entry.insert(0, id_str)
            
            # 2. Trigger the search function 
            self.filter_fragrances()
            
            messagebox.showinfo("Scan Complete", f"Fragrance ID {id_str} found and searched.")
        else:
            messagebox.showinfo("Scan Result", "No valid Fragrance ID found or scan cancelled.")       
    # ---------------- UTILITY: VALIDATION ----------------
    def validate_numeric_input(self, value, field_name, is_integer=False):
        """Checks if a string can be converted to a number, returning None on failure."""
        value = str(value).strip()
        
        if not value or value.isspace():
            return 0 if is_integer else 0.0 # Treat empty/whitespace numeric fields as zero
        
        try:
            # Attempt to clean up currency formatting if it's accidentally passed
            if isinstance(value, str):
                value = value.replace('$', '').replace(',', '').replace('£', '')
                
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
        self.populate_fragrances() # Replaced the three populate_table calls
        self.populate_customers()
        self.populate_sales()
        self.populate_supplies()
        self.populate_oils()
        self.populate_expenses()
        self.update_fragrance_viewer(self.selected_id)

    # ---------------- FRAGRANCE LOGIC ----------------
    # --- OLD populate_table METHOD DELETED ---

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
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete fragrance: {name} (ID: {self.selected_id})? This may affect historical sales records."):
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
        # --- SYNTAX ERROR LINE REMOVED FROM HERE ---
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
        # RIGHT SIDE: Image Viewer
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
        # FIXED: Replaced men/women/unisex tabs with a single fragrance_tab
        self.fragrance_tab = ttk.Frame(self.tabControl) # NEW
        self.customer_tab = ttk.Frame(self.tabControl)
        self.sales_tab = ttk.Frame(self.tabControl)
        self.supplies_tab = ttk.Frame(self.tabControl)
        self.oils_tab = ttk.Frame(self.tabControl)
        self.expenses_tab = ttk.Frame(self.tabControl)
        self.chart_tab = ttk.Frame(self.tabControl)
        # FIXED: Updated tabControl.add calls
        self.tabControl.add(self.fragrance_tab, text="Fragrances") # NEW
        self.tabControl.add(self.customer_tab, text="Customers")
        self.tabControl.add(self.sales_tab, text="Sales")
        self.tabControl.add(self.supplies_tab, text="Supplies")
        self.tabControl.add(self.oils_tab, text="Oils")
        self.tabControl.add(self.expenses_tab, text="Expenses")
        self.tabControl.add(self.chart_tab, text="Profit Chart")
        # FIXED: Updated setup calls
        self.setup_fragrance_tab(self.fragrance_tab, "All") # NEW
        self.setup_customer_tab(self.customer_tab) 
        self.setup_sales_tab(self.sales_tab)
        self.setup_supplies_tab(self.supplies_tab)
        self.setup_oils_tab(self.oils_tab)
        self.setup_expenses_tab(self.expenses_tab)
        self.setup_chart_tab(self.chart_tab)
        
        # Bind tab change event
        self.tabControl.bind("<<NotebookTabChanged>>", self.on_tab_change)

    # --- MODIFIED: on_tab_change ---
    def on_tab_change(self, event):
        """
        Refreshes content for the selected tab.
        """
        selected_tab_text = self.tabControl.tab(self.tabControl.select(), "text")
        
        # FIXED: Check the new single fragrance tree
        if self.fragrances_tree:
            self.fragrances_tree.selection_set("") 

        self.selected_id = None
        
        # Refresh the data for the newly selected tab
        if selected_tab_text == "Profit Chart":
            self.update_chart_tab() # New master function for this tab
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
        # FIXED: Updated to check for new "Fragrances" tab
        elif selected_tab_text == "Fragrances":
             self.populate_fragrances()

    # --- OLD search_fragrance METHOD DELETED ---

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
            if edit and f_data and i < 9:
                db_index = i + 1
                value = f_data[db_index] if db_index < len(f_data) and f_data[db_index] is not None else ""
                
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

        def save():
            name = entries["Name"].get().strip()
            desc = entries["Description"].get().strip()
            gender = entries["Gender"].get().strip()
            category = entries["Category"].get().strip()
            inspired_by = entries["Inspired By"].get().strip()
            
            unit_cost = self.validate_numeric_input(entries["Unit Cost"].get(), "Unit Cost", is_integer=False)
            sale_price = self.validate_numeric_input(entries["Sale Price"].get(), "Sale Price", is_integer=False)
            quantity = self.validate_numeric_input(entries["Quantity"].get(), "Quantity", is_integer=True)
            image_path = entries["Image"].get().strip()
            
            if None in (unit_cost, sale_price, quantity) or not name or not gender:
                messagebox.showerror("Input Error", "Name, Gender, and valid numbers for cost/quantity are required.")
                return

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
            
        ttk.Button(form_frame, text=("Save Changes" if edit else "Add Fragrance"), 
                   command=save, style='Primary.TButton').grid(row=9, column=1, pady=10, sticky="e")
        form_frame.grid_columnconfigure(1, weight=1)

    # ---------------- FRAGRANCE TAB SETUP (REFACTORED) ----------------
    def setup_fragrance_tab(self, parent, gender_type):
        """Sets up the Fragrances tab layout, table, and controls.
        
        :param parent: The Tkinter notebook tab frame.
        :param gender_type: The gender associated with this tab (e.g., "Men", "Women").
        """
        
        # NOTE: Although 'gender_type' is passed, it is not used in the 
        # UI setup below as the filter dropdown handles gender filtering.
        # However, we must accept it to match the function call.
        
        # --- Filter and Search Frame ---
        filter_frame = ttk.Frame(parent, padding="5 5 5 0")
        filter_frame.pack(fill="x")
        
        # Search Entry and Button
        ttk.Label(filter_frame, text="Search Fragrances:").pack(side="left", padx=(0, 5))
        self.fragrances_search_entry = ttk.Entry(filter_frame, style='TEntry')
        self.fragrances_search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        # Bind the search filter to key release events for dynamic filtering
        self.fragrances_search_entry.bind('<KeyRelease>', lambda e: self.filter_fragrances())
        
        # --- QR Scan Button ---
        ttk.Button(filter_frame, 
                   text="📷 Scan QR Code", 
                   command=self.scan_and_search_fragrance, 
                   style='Modern.TButton').pack(side="left", padx=(5, 10))
        # ----------------------
        
        # Gender Filter Dropdown
        ttk.Label(filter_frame, text="Filter by Gender:").pack(side="left", padx=(10, 5))
        # FIXED: Values changed from "Male"/"Female" to "Men"/"Women" to match DB
        self.fragrances_gender_filter = ttk.Combobox(filter_frame, values=["All", "Men", "Women", "Unisex"], state="readonly", width=10)
        self.fragrances_gender_filter.set("All")
        self.fragrances_gender_filter.bind("<<ComboboxSelected>>", lambda e: self.filter_fragrances())
        self.fragrances_gender_filter.pack(side="left")

        # --- Table Setup ---
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # FIXED: Columns updated to match database schema and old populate_table logic
        columns = ("ID", "Name", "Gender", "Category", "Unit Cost", "Sale Price", "Inspired By", "Quantity")
        self.fragrances_tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        
        # FIXED: Column definitions updated
        self.fragrances_tree.column("ID", width=40, anchor="center")
        self.fragrances_tree.column("Name", width=180)
        self.fragrances_tree.column("Gender", width=80, anchor="center")
        self.fragrances_tree.column("Category", width=120)
        self.fragrances_tree.column("Unit Cost", width=80, anchor="e")
        self.fragrances_tree.column("Sale Price", width=80, anchor="e")
        self.fragrances_tree.column("Inspired By", width=180)
        self.fragrances_tree.column("Quantity", width=60, anchor="center")
        
        for col in columns: self.fragrances_tree.heading(col, text=col)
        
        # --- CORRECTED LINE ADDED HERE ---
        self.fragrances_tree.tag_configure('low_stock', foreground=LOW_STOCK_COLOR)
        # ---------------------------------
        
        self.fragrances_tree.pack(side="left", fill="both", expand=True)
        self.fragrances_tree.bind("<<TreeviewSelect>>", self.on_fragrance_select)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.fragrances_tree.yview)
        self.fragrances_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # --- Button Frame ---
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(btn_frame, text="➕ Add Fragrance", command=lambda: self.open_fragrance_form(edit=False), style='Primary.TButton').pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✏️ Edit Selected", command=lambda: self.open_fragrance_form(edit=True), style='Modern.TButton').pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ Delete Selected", command=self.delete_fragrance_record, style='Modern.TButton').pack(side="left", padx=5)
        ttk.Button(btn_frame, text="📦 Record Sale", command=self.open_sale_form, style='Modern.TButton').pack(side="left", padx=5)

        # Initialize the table population
        self.populate_fragrances() # This method will be added next

    # ---------------- NEW/REBUILT FRAGRANCE METHODS ----------------

    def populate_fragrances(self, event=None):
        """Wrapper to populate the main fragrance tree."""
        # This just calls the filter function, which handles all population
        self.filter_fragrances()

    def filter_fragrances(self, event=None):
        """Filters the fragrance tree based on search and gender dropdown."""
        if not self.fragrances_tree:
            return

        try:
            # Get filter values from the widgets
            search_term = self.fragrances_search_entry.get().strip().lower()
            gender_filter = self.fragrances_gender_filter.get()
        except Exception:
            return # Widgets may not be ready yet

        # Clear the tree
        for row in self.fragrances_tree.get_children():
            self.fragrances_tree.delete(row)

        # Get all fragrances from DB
        all_fragrances = get_all_fragrances() 

        # Apply filters
        filtered_list = []
        for f in all_fragrances:
            # DB Schema: (id[0], name[1], desc[2], gender[3], cat[4], u_cost[5], s_price[6], inspired[7], qty[8], img_path[9])
            
            # 1. Gender Filter
            if gender_filter != "All" and f[3] != gender_filter:
                continue
            
            # 2. Search Filter (checks ID, Name, and Inspired By)
            if search_term:
                f_id = str(f[0])
                f_name = str(f[1] or "").lower()
                f_inspired = str(f[7] or "").lower()
                
                if (search_term not in f_id and
                    search_term not in f_name and
                    search_term not in f_inspired):
                    continue
            
            # If it passes all filters, add to list
            filtered_list.append(f)

        # Populate the tree with the filtered list
        for i, f in enumerate(filtered_list):
            tags = ()
            quantity = int(f[8] or 0) # f[8] is quantity, safely defaulted to 0
            if quantity <= 5: 
                tags = ('low_stock',)
            
            # --- FIX APPLIED HERE: Using (f[5] or 0.0) and (f[6] or 0.0) ---
            # This handles empty strings or None by defaulting to 0.0 before conversion.
            unit_cost = f"{float(f[5] or 0.0):.2f}"
            sale_price = f"{float(f[6] or 0.0):.2f}"
            # --------------------------------------------------------------------------
            
            # Columns: ("ID", "Name", "Gender", "Category", "Unit Cost", "Sale Price", "Inspired By", "Quantity")
            self.fragrances_tree.insert("", "end", iid=str(f[0]), tags=tags, 
                                values=(f[0], f[1], f[3], f[4], unit_cost, sale_price, f[7], quantity))

    def search_from_top_bar(self):
        """Takes text from top search bar, puts it in the in-tab search, and filters."""
        search_term = self.search_entry.get()
        
        if self.fragrances_search_entry:
            # 1. Put text in the tab's search bar
            self.fragrances_search_entry.delete(0, tk.END)
            self.fragrances_search_entry.insert(0, search_term)
        
        try:
            # 2. Switch to the fragrance tab
            self.tabControl.select(self.fragrance_tab)
        except tk.TclError:
            pass # Tab already selected or doesn't exist
            
        # 3. Trigger the filter
        self.filter_fragrances()

    # ---------------- END NEW METHODS ----------------
    
    # ---------------- CUSTOMER LOGIC ----------------
    def on_customer_select(self, event):
        """Sets the selected_customer_id when a customer is selected."""
        tree = event.widget
        selected_item = tree.focus()
        if selected_item:
            self.selected_customer_id = int(tree.item(selected_item)['values'][0])
        else:
            self.selected_customer_id = None
            
    def setup_customer_tab(self, parent):
        """Sets up the UI for the Customers tab."""
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
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete customer: {name} (ID: {self.selected_customer_id})? This may affect historical sales records."):
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
            
            qty = self.validate_numeric_input(qty_entry.get(), "Quantity", is_integer=True)
            if qty is None: return
            if qty <= 0:
                messagebox.showerror("Error", "Quantity must be a positive number")
                return
            
            current_qty = int(fragrance[8] or 0)
            if qty > current_qty:
                messagebox.showerror("Error", f"Not enough stock. Available: {current_qty}")
                return
            
            customer_id = int(customer_var.get().split("ID:")[1].replace(")", ""))
            unit_cost = float(fragrance[5])
            sale_price = float(fragrance[6])
            revenue = sale_price * qty
            profit = (sale_price - unit_cost) * qty
            date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            insert_sale((self.selected_id, customer_id, qty, unit_cost, sale_price, revenue, profit, date))
            update_fragrance_quantity(self.selected_id, current_qty - qty)
            
            self.populate_sales()
            self.refresh_all_tables()
            self.update_fragrance_viewer(self.selected_id)
            form.destroy()

        ttk.Button(form_frame, text="Save Sale", command=save_sale, style='Primary.TButton').grid(row=3, column=1, pady=10, sticky="e")
        form_frame.grid_columnconfigure(1, weight=1)
        
    def setup_sales_tab(self, parent):
        """Sets up the UI for the Sales tab."""
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
            
        all_sales = get_all_sales()
        
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
                # The get_sales_by_month function expects (month, year) as separate args
                year_str, month_str = selected_month_year.split('-')
                sales = get_sales_by_month(int(month_str), int(year_str))
            except ValueError:
                sales = [] 
            except Exception as e:
                print(f"Error filtering sales: {e}")
                sales = []

        for s in sales:
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
        
        # --- NEW BUTTON ADDED ---
        ttk.Button(btn_frame, text="💰 Record Purchase", command=self.record_supply_purchase, style='Modern.TButton').pack(side="right", padx=5)
        # ------------------------
        
        self.populate_supplies()

    def populate_supplies(self):
        if not self.supplies_tree: return
        for row in self.supplies_tree.get_children(): self.supplies_tree.delete(row)
        supplies = get_all_supplies()
        # Supply DB structure: (id, name, price, purchase_link, quantity)
        for s in supplies:
            price_val = s[2] if s[2] is not None else 0.0
            self.supplies_tree.insert("", "end", values=(s[0], s[1], f"{price_val:.2f}", s[3], s[4]))
            
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
                value = s_data[i+1]
                if field == "Price":
                    try: value = f"{float(value):.2f}"
                    except: value = "0.00"
                entry.insert(0, str(value) if value is not None else "")
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
        
        # --- NEW BINDING ADDED FOR COPY-PASTE ---
        self.oils_tree.bind("<Double-1>", self.copy_oil_link)
        # ----------------------------------------

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.oils_tree.yview)
        self.oils_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="➕ Add Oil", command=lambda: self.open_oil_form(edit=False), style='Primary.TButton').pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✏️ Edit Selected", command=lambda: self.open_oil_form(edit=True), style='Modern.TButton').pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ Delete Selected", command=self.delete_oil_record, style='Modern.TButton').pack(side="left", padx=5)
        
        ttk.Button(btn_frame, text="💰 Record Purchase", command=self.record_oil_purchase, style='Modern.TButton').pack(side="right", padx=5)
        
        self.populate_oils()

    def populate_oils(self):
        if not self.oils_tree: return
        for row in self.oils_tree.get_children(): self.oils_tree.delete(row)
        oils = get_all_oils()

        def safe_float_format(value):
            if value is None or str(value).strip() == '':
                return "0.00"
            try:
                return f"{float(value):.2f}"
            except (ValueError, TypeError):
                return "0.00"
        
        # Oils DB structure: (id, name, size, price, purchase_link, quantity)
        for o in oils:
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
                value = o_data[i+1]
                if field in ["Size (ml)", "Price"]:
                    try: value = f"{float(value):.2f}"
                    except: value = "0.00"
                entry.insert(0, str(value) if value is not None else "")
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

    # ---------------- OPEN SALE FORM (FIXED) ----------------
    def open_sale_form(self):
        """Opens a form to record a new sale for the selected fragrance."""
        
        # 1. Check if a fragrance is selected
        # FIXED: Changed self.selected_fragrance_id to self.selected_id
        if not self.selected_id:
            messagebox.showwarning("No Selection", "Please select a fragrance to record a sale for.")
            return

        # 2. Retrieve selected fragrance details to pre-fill the form
        try:
            # FIXED: Changed self.selected_fragrance_id to self.selected_id
            f_data = get_fragrance_by_id(self.selected_id) 
        except Exception:
            messagebox.showerror("Database Error", "Could not retrieve fragrance details.")
            return
            
        if not f_data:
            messagebox.showerror("Error", "Selected fragrance item not found in database.")
            return
            
        # DB Schema: (id[0], name[1], desc[2], gender[3], cat[4], u_cost[5], s_price[6], inspired[7], qty[8], img_path[9])
        fragrance_name = f_data[1]  # Index 1 is the name
        # FIXED: Changed f_data[3] to f_data[6] (Sale Price)
        unit_price = float(f_data[6] or 0.0) 

        # 3. Create the Form Window
        form = tk.Toplevel(self.root)
        form.title(f"Record Sale: {fragrance_name}")
        form.geometry("450x350")
        form.config(bg=BG_LIGHT)
        form_frame = ttk.Frame(form, padding=15)
        form_frame.pack(fill="both", expand=True)

        fields = ["Fragrance Name", "Quantity Sold", "Sale Price (per unit)", "Customer Name (Optional)"]
        entries = {}

        for i, field in enumerate(fields):
            ttk.Label(form_frame, text=f"{field}:").grid(row=i, column=0, padx=5, pady=5, sticky="w")
            entry = ttk.Entry(form_frame, style='TEntry')
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            entries[field] = entry
            
            if field == "Fragrance Name":
                entry.insert(0, fragrance_name)
                entry.config(state='readonly')
            elif field == "Sale Price (per unit)" and unit_price != 0.0:
                entry.insert(0, f"{unit_price:.2f}")
            elif field == "Quantity Sold":
                entry.insert(0, "1")

        # 4. Save Logic
        def save():
            quantity_sold = self.validate_numeric_input(entries["Quantity Sold"].get(), "Quantity Sold", is_integer=True)
            sale_price = self.validate_numeric_input(entries["Sale Price (per unit)"].get(), "Sale Price (per unit)", is_integer=False)
            customer_name = entries["Customer Name (Optional)"].get().strip()
            
            if quantity_sold is None or sale_price is None:
                return 

            if quantity_sold <= 0:
                messagebox.showerror("Input Error", "Quantity Sold must be greater than zero.")
                return

            total_sale = sale_price * quantity_sold 
            sale_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # (fragrance_id, quantity, unit_price, total_sale, customer, date)
            # FIXED: Changed self.selected_fragrance_id to self.selected_id
            data_to_insert = (self.selected_id, quantity_sold, sale_price, total_sale, customer_name, sale_date)
            
            try:
                # 1. Record the sale
                # NOTE: This assumes your `insert_sale` function matches this tuple structure
                # (self.selected_id, quantity_sold, sale_price, total_sale, customer_name, sale_date)
                # Your *other* sale logic (record_sale) uses a different structure.
                # We will use the structure from *this* function, assuming it's the intended one.
                
                # --- RE-FIXING based on your `database.py` imports and `record_sale` function ---
                # The `insert_sale` function likely expects the 8-tuple structure.
                
                customer_id = None # This simple form doesn't select a customer ID
                unit_cost = float(f_data[5] or 0.0) # Get unit cost
                revenue = total_sale # `total_sale` is the same as `revenue`
                profit = (sale_price - unit_cost) * quantity_sold
                date = sale_date
                
                # This is the 8-tuple structure matching `record_sale`
                # (fragrance_id, customer_id, qty, unit_cost, sale_price, revenue, profit, date)
                # We use `None` for customer_id as this form doesn't select one.
                data_to_insert_v2 = (self.selected_id, customer_id, quantity_sold, unit_cost, sale_price, revenue, profit, date)

                insert_sale(data_to_insert_v2)
                
                # 2. Update the fragrance inventory quantity (decrement stock)
                # FIXED: Changed f_data[4] to f_data[8] (Quantity)
                current_stock = int(f_data[8] or 0) 
                new_stock = current_stock - quantity_sold
                    
                # FIXED: Changed self.selected_fragrance_id to self.selected_id
                update_fragrance_quantity(self.selected_id, new_stock)
                
                messagebox.showinfo("Success", f"Sale of {quantity_sold} units recorded. Stock updated to {new_stock}.")
                
                # 3. Refresh UI
                self.populate_fragrances() # This now exists
                self.populate_sales() 
                self.update_chart_tab()
                form.destroy()
                
            except Exception as e:
                messagebox.showerror("Database Error", f"Could not record sale or update inventory: {e}")
                
        ttk.Button(form_frame, text="Record Sale", command=save, style='Primary.TButton').grid(row=len(fields), column=1, pady=15, sticky="e")
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

    # ---------------- EXPENSE TAB SETUP AND LOGIC ----------------
    def setup_expenses_tab(self, parent):
        # Top Frame for Monthly Summary and Add Button
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill="x", padx=5, pady=5)
        
        # Monthly Total Display and Filter
        summary_frame = ttk.LabelFrame(top_frame, text="Monthly Summary", padding=10, style='Viewer.TLabelframe')
        summary_frame.pack(side="left", padx=10)
        
        self.expense_month_var.set("All Months") # Use the class variable
        
        self.expense_month_filter = ttk.Combobox(summary_frame, textvariable=self.expense_month_var, state="readonly", width=15, style='TCombobox')
        self.expense_month_filter.pack(side="left", padx=5)
        self.expense_month_filter.bind("<<ComboboxSelected>>", self.filter_expenses_by_month) 
        
        self.total_expense_label = ttk.Label(summary_frame, text="Total Expenses: £0.00", style='Bold.TLabel', background=BG_SECONDARY)
        self.total_expense_label.pack(side="left", padx=15)
        
        # Add Expense Button
        btn_frame = ttk.Frame(top_frame)
        btn_frame.pack(side="right", padx=5)
        ttk.Button(btn_frame, text="➕ Record Expense", command=self.open_expense_form, style='Primary.TButton').pack(side="right", padx=5)

        # Table Frame
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Columns for the new 7-column display
        columns = ("ID", "Date", "Item Name", "Cost", "Quantity", "Supplier", "Total Cost")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        tree.column("ID", width=40, anchor="center")
        tree.column("Date", width=150, anchor="center")
        tree.column("Item Name", width=250)
        tree.column("Cost", width=100, anchor="center")      # Unit Cost
        tree.column("Quantity", width=80, anchor="center")
        tree.column("Supplier", width=200)
        tree.column("Total Cost", width=120, anchor="center") # Amount

        for col in columns:
            tree.heading(col, text=col)
        
        tree.pack(side="left", fill="both", expand=True)
        self.expenses_tree = tree
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        self.populate_expenses() # Initial population

    def open_expense_form(self, item_name="", unit_cost=0.0, quantity=1):
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
            
            # --- START NEW/MODIFIED LOGIC ---
            if field == "Item Name":
                entry.insert(0, item_name)
            elif field == "Cost (per item)" and unit_cost != 0.0:
                entry.insert(0, f"{unit_cost:.2f}")
            elif field == "Quantity" and quantity != 1:
                entry.insert(0, str(quantity))
            # --- END NEW/MODIFIED LOGIC ---
            
        def save():
            # ... (rest of the save function is unchanged)
            item_name = entries["Item Name"].get().strip()
            supplier = entries["Supplier (Optional)"].get().strip()
            
            if not item_name:
                messagebox.showerror("Input Error", "Item Name is required.")
                return

            cost = self.validate_numeric_input(entries["Cost (per item)"].get(), "Cost (per item)", is_integer=False)
            quantity = self.validate_numeric_input(entries["Quantity"].get(), "Quantity", is_integer=True)
            
            if cost is None or quantity is None:
                return 

            if cost <= 0 or quantity <= 0:
                messagebox.showerror("Input Error", "Cost and Quantity must be greater than zero for a new expense.")
                return

            total_cost = cost * quantity 
            expense_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # (item_name, unit_cost, quantity, supplier, total_cost, date)
            data_to_insert = (item_name, cost, quantity, supplier, total_cost, expense_date)
            
            try:
                insert_expense(data_to_insert)
                
                messagebox.showinfo("Success", "Expense recorded.")
                self.populate_expenses() # Refresh table
                self.update_chart_tab() # Refresh chart data
                form.destroy()
            except Exception as e:
                messagebox.showerror("Database Error", f"Could not record expense: {e}")
                
        ttk.Button(form_frame, text="Save Expense", command=save, style='Primary.TButton').grid(row=len(fields), column=1, pady=15, sticky="e")
        form_frame.grid_columnconfigure(1, weight=1)
        # ---------------- SUPPLIES LOGIC (Addition) ----------------

    def record_supply_purchase(self):
        """Records a purchase expense for the selected supply item."""
        if not self.selected_supply_id:
            messagebox.showwarning("No Selection", "Please select a supply item to record a purchase for.")
            return

        # s_data is (id, name, price, purchase_link, quantity)
        s_data = get_supply_by_id(self.selected_supply_id) 
        if not s_data:
            messagebox.showerror("Error", "Supply item not found.")
            return

        item_name = s_data[1]
        unit_cost = float(s_data[2] or 0.0) # Price
        # We don't use s_data[4] (current stock quantity) as the default, 
        # because a new purchase could be for any amount. Default to 1.
        
        self.open_expense_form(item_name=item_name, unit_cost=unit_cost, quantity=1)


    # ---------------- OILS LOGIC (Addition) ----------------

    def record_oil_purchase(self):
        """Records a purchase expense for the selected oil item."""
        if not self.selected_oil_id:
            messagebox.showwarning("No Selection", "Please select an oil item to record a purchase for.")
            return

        # o_data is (id, name, size, price, purchase_link, quantity)
        o_data = get_oil_by_id(self.selected_oil_id) 
        if not o_data:
            messagebox.showerror("Error", "Oil item not found.")
            return

        # Combine name and size for clarity in the expense record
        item_name = f"{o_data[1]} ({o_data[2]}ml)" if o_data[2] else o_data[1]
        unit_cost = float(o_data[3] or 0.0) # Price
        
        # We don't use o_data[5] (current stock quantity) as the default. Default to 1.
        
        self.open_expense_form(item_name=item_name, unit_cost=unit_cost, quantity=1)    

    def populate_expenses(self):
        if not self.expenses_tree:
            return
            
        for i in self.expenses_tree.get_children():
            self.expenses_tree.delete(i)
            
        if not self.expense_month_filter:
            return # Avoids error on init if filter not ready

        try:
            all_expenses = get_all_expenses()

            # --- Update Month Filter ---
            # DB fields: id[0], name[1], desc[2], amount[3], date[4], unit_cost[5], qty[6], supplier[7]
            month_strings = [e[4][:7] for e in all_expenses if e[4]]
            months = sorted(list(set(month_strings)), reverse=True)
            
            current_selection = self.expense_month_var.get()
            self.expense_month_filter['values'] = ["All Months"] + months
            if current_selection not in (["All Months"] + months):
                self.expense_month_var.set("All Months")

            # --- Filter Data Based on Selection ---
            selected_month = self.expense_month_var.get()
            if selected_month == "All Months":
                filtered_expenses = all_expenses
            else:
                filtered_expenses = [e for e in all_expenses if e[4] and e[4].startswith(selected_month)]

            # --- Populate the Treeview ---
            total_expense_sum = 0
            for expense in filtered_expenses:
                # DB fields: id[0], name[1], desc[2], amount[3], date[4], unit_cost[5], qty[6], supplier[7]
                
                exp_id = expense[0]
                exp_date = expense[4].split(" ")[0] if expense[4] else "N/A"
                item_name = expense[1]
                
                unit_cost = f"£{expense[5]:.2f}" if expense[5] is not None else "N/A"
                quantity = expense[6] if expense[6] is not None else "N/A"
                supplier = expense[7] if expense[7] else "N/A"
                
                total_cost_val = expense[3] if expense[3] is not None else 0.0
                total_cost_str = f"£{total_cost_val:.2f}"

                # Tree Columns: ("ID", "Date", "Item Name", "Cost", "Quantity", "Supplier", "Total Cost")
                self.expenses_tree.insert("", "end", values=(
                    exp_id,
                    exp_date,
                    item_name,
                    unit_cost,
                    quantity,
                    supplier,
                    total_cost_str
                ))
                
                total_expense_sum += total_cost_val

            self.total_expense_label.config(text=f"TOTAL EXPENSES: £{total_expense_sum:.2f}")

        except Exception as e:
            messagebox.showerror("Expense Data Error", f"Failed to load expenses: {e}")

    def filter_expenses_by_month(self, event=None):
        """Called when the combobox selection changes."""
        self.populate_expenses()

    # ---------------- PROFIT CHART TAB (UPDATED) ----------------
    
    # --- UPDATED: setup_chart_tab ---
    def setup_chart_tab(self, parent):
        # --- 1. Top Control Frame (for the new filter) ---
        top_controls_frame = ttk.Frame(parent)
        top_controls_frame.pack(fill="x", padx=10, pady=(5, 0))

        ttk.Label(top_controls_frame, text="Select Period:", style='Bold.TLabel').pack(side="left", padx=(0, 5))
        
        self.chart_month_selector = ttk.Combobox(top_controls_frame, state="readonly", width=18, style='TCombobox')
        self.chart_month_selector.pack(side="left")
        # Bind the selector to the new update function
        self.chart_month_selector.bind("<<ComboboxSelected>>", self.update_chart_tab)
        
        # --- 2. Main Area (for Graph and Summary) ---
        main_chart_area_frame = ttk.Frame(parent)
        main_chart_area_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # --- 3. Graph Frame (will hold the canvas) ---
        self.graph_frame = ttk.Frame(main_chart_area_frame)
        self.graph_frame.pack(side="left", fill="both", expand=True)

        # --- 4. Summary Panel (on the right) ---
        summary_panel = ttk.Frame(main_chart_area_frame, width=350)
        summary_panel.pack(side="right", fill="y", padx=(15, 0))
        summary_panel.pack_propagate(False) # Prevents frame from shrinking

        # --- Summary Group 1: Monthly Snapshot ---
        monthly_summary_frame = ttk.LabelFrame(summary_panel, text="Snapshot", style='Viewer.TLabelframe', padding=15)
        monthly_summary_frame.pack(fill="x", pady=(0, 10))

        # We need labels to update, so we make them class attributes
        self.summary_revenue_label = self.create_summary_row(monthly_summary_frame, "Total Revenue:", "£0.00", 0)
        self.summary_cogs_label = self.create_summary_row(monthly_summary_frame, "Cost of Goods (COGS):", "£0.00", 1)
        self.summary_overhead_label = self.create_summary_row(monthly_summary_frame, "Overhead Expenses:", "£0.00", 2)
        
        # Add a separator
        ttk.Separator(monthly_summary_frame, orient='horizontal').grid(row=3, column=0, columnspan=2, sticky='ew', pady=8)
        
        # The final profit label (make it bold)
        ttk.Label(monthly_summary_frame, text="Net Profit:", font=('Arial', 11, 'bold'), background=BG_SECONDARY).grid(row=4, column=0, sticky='w', pady=(5,0))
        self.summary_profit_label = ttk.Label(monthly_summary_frame, text="£0.00", font=('Arial', 11, 'bold'), background=BG_SECONDARY, anchor='e')
        self.summary_profit_label.grid(row=4, column=1, sticky='e', pady=(5,0))

        # --- Summary Group 2: Total Inventory (Live Data) ---
        inventory_summary_frame = ttk.LabelFrame(summary_panel, text="Total Inventory (Current)", style='Viewer.TLabelframe', padding=15)
        inventory_summary_frame.pack(fill="x", pady=10)
        
        self.summary_total_stock_label = self.create_summary_row(inventory_summary_frame, "Total Fragrances:", "0", 0)
        self.summary_total_value_label = self.create_summary_row(inventory_summary_frame, "Total Stock Value (Cost):", "£0.00", 1) # Label text updated
        
        # --- NEW ROW ADDED ---
        self.summary_retail_value_label = self.create_summary_row(inventory_summary_frame, "Total Retail Value:", "£0.00", 2) 
        # ---------------------
        
        # Configure columns for right-alignment
        monthly_summary_frame.grid_columnconfigure(1, weight=1)
        inventory_summary_frame.grid_columnconfigure(1, weight=1)

    # --- NEW: create_summary_row (Helper Function) ---
    def create_summary_row(self, parent, text, default_value, row):
        """Helper to create a text-label and a value-label row."""
        ttk.Label(parent, text=text, background=BG_SECONDARY).grid(row=row, column=0, sticky='w')
        value_label = ttk.Label(parent, text=default_value, background=BG_SECONDARY, anchor='e', style='Bold.TLabel')
        value_label.grid(row=row, column=1, sticky='ew')
        return value_label
        
    # --- MODIFIED: update_chart_tab (Master Function) ---
    def update_chart_tab(self, event=None):
        """
        Master function to refresh all data on the Profit Chart tab.
        This calculates summary stats AND calls the plot function.
        """
        
        # --- 1. Update Inventory Summary (Always Live) ---
        try:
            all_fragrances = get_all_fragrances()
            total_stock = 0
            total_cost_value = 0.0 # Renamed for clarity
            total_retail_value = 0.0 # NEW variable
            
            for f in all_fragrances:
                # f[8] = quantity, f[5] = unit_cost, f[6] = sale_price
                stock = f[8] or 0
                cost = f[5] or 0.0
                sale_price = f[6] or 0.0 # Get sale price
                
                total_stock += stock
                total_cost_value += (stock * cost)
                total_retail_value += (stock * sale_price) # Calculate Retail Value
            
            self.summary_total_stock_label.config(text=f"{total_stock} units")
            self.summary_total_value_label.config(text=f"£{total_cost_value:.2f}") # Uses cost value
            self.summary_retail_value_label.config(text=f"£{total_retail_value:.2f}") # Updates new retail value label
        except Exception as e:
            print(f"Error calculating inventory: {e}")
            self.summary_total_stock_label.config(text="Error")
            self.summary_total_value_label.config(text="Error")
            self.summary_retail_value_label.config(text="Error") # Error handler for new label

        # --- 2. Get All Financial Data & Populate Filter ---
        try:
            all_sales = get_all_sales()
            all_expenses = get_all_expenses()
            
            # Get the processed monthly data
            financial_data = self.get_financial_data(all_sales, all_expenses)
            
            # Populate the month selector
            months = sorted(financial_data.keys(), reverse=True)
            current_selection = self.chart_month_selector.get()
            self.chart_month_selector['values'] = ["All Time"] + months
            
            # Ensure selection is valid
            if not current_selection or current_selection not in (["All Time"] + months):
                self.chart_month_selector.set("All Time")
            
            selected_period = self.chart_month_selector.get()

            # --- 3. Update Summary Panel based on selection ---
            if selected_period == "All Time":
                # Sum all months
                total_revenue = sum(data['revenue'] for data in financial_data.values())
                total_cogs = sum(data['cogs'] for data in financial_data.values())
                total_overhead = sum(data['overhead'] for data in financial_data.values())
                total_profit = sum(data['profit'] for data in financial_data.values())
            else:
                # Get specific month
                data = financial_data.get(selected_period, {'revenue': 0, 'cogs': 0, 'overhead': 0, 'profit': 0})
                total_revenue = data['revenue']
                total_cogs = data['cogs']
                total_overhead = data['overhead']
                total_profit = data['profit']

            # Set the label text
            self.summary_revenue_label.config(text=f"£{total_revenue:.2f}")
            self.summary_cogs_label.config(text=f"£{total_cogs:.2f}")
            self.summary_overhead_label.config(text=f"£{total_overhead:.2f}")
            self.summary_profit_label.config(text=f"£{total_profit:.2f}")
            
            # --- 4. Call the Plot Function ---
            self.plot_profit_chart(financial_data, selected_period)

        except Exception as e:
            messagebox.showerror("Chart Error", f"Could not load chart data: {e}")
            print(f"Update Chart Tab Error: {e}")

    # --- NEW: get_financial_data (Helper Function) ---
    def get_financial_data(self, all_sales, all_expenses):
        """
        Helper function to process raw sales/expense data into a clean monthly dictionary.
        Returns: {'YYYY-MM': {'revenue': X, 'cogs': Y, 'overhead': Z, 'profit': P}, ...}
        """
        overhead_data = {}
        # DB: id[0], name[1], desc[2], amount[3], date[4], unit_cost[5], qty[6], supplier[7]
        for e in all_expenses:
            date_str = e[4] # Date
            if date_str:
                month_key = date_str[:7]
                total_cost = float(e[3] or 0.0) # amount
                overhead_data[month_key] = overhead_data.get(month_key, 0.0) + total_cost

        sales_data = {}
        # sales: (s.id, f.name, c.name, s.qty_sold, s.unit_cost, s.sale_price, s.revenue, s.profit, s.date)
        for sale in all_sales:
            date_str = sale[8] # Date
            if date_str:
                month_key = date_str[:7]
                revenue = float(sale[6] or 0.0)
                cogs = float(sale[4] or 0.0) * float(sale[3] or 0.0) # unit_cost * qty_sold
                
                if month_key not in sales_data:
                    sales_data[month_key] = {'revenue': 0.0, 'cogs': 0.0}
                
                sales_data[month_key]['revenue'] += revenue
                sales_data[month_key]['cogs'] += cogs
                
        # Combine all data
        all_months = sorted(list(set(sales_data.keys()) | set(overhead_data.keys())))
        
        final_data = {}
        for month in all_months:
            revenue = sales_data.get(month, {}).get('revenue', 0.0)
            cogs = sales_data.get(month, {}).get('cogs', 0.0)
            overhead = overhead_data.get(month, 0.0)
            profit = revenue - (cogs + overhead)
            
            final_data[month] = {
                'revenue': revenue,
                'cogs': cogs,
                'overhead': overhead,
                'profit': profit
            }
        return final_data

    # --- MODIFIED: plot_profit_chart ---
    def plot_profit_chart(self, financial_data, selected_period):
        """
        Draws the profit chart based on pre-calculated data and the selected period.
        """
        # Clear previous chart
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
            
        if not financial_data:
            ttk.Label(self.graph_frame, text="No sales or expense data available to plot.", font=('Arial', 12, 'italic')).pack(pady=50)
            return

        try:
            # --- Prepare data based on selected period ---
            if selected_period == "All Time":
                all_months = sorted(financial_data.keys())
                revenue = [financial_data[m]['revenue'] for m in all_months]
                sales_cogs = [financial_data[m]['cogs'] for m in all_months]
                general_expenses = [financial_data[m]['overhead'] for m in all_months]
                profit = [financial_data[m]['profit'] for m in all_months]
                plot_title = "Monthly Financial Summary (All Time)"
            else:
                # Plotting for a single selected month
                data = financial_data.get(selected_period, {'revenue': 0, 'cogs': 0, 'overhead': 0, 'profit': 0})
                all_months = [selected_period]
                revenue = [data['revenue']]
                sales_cogs = [data['cogs']]
                general_expenses = [data['overhead']]
                profit = [data['profit']]
                plot_title = f"Financial Summary for {selected_period}"
            
            # --- Plotting with Matplotlib ---
            plt.style.use('seaborn-v0_8-notebook') 
            fig, ax1 = plt.subplots(figsize=(10, 5))
            
            width = 0.25
            x = np.arange(len(all_months))

            rects1 = ax1.bar(x - width, revenue, width, label='Total Revenue', color='#4CAF50')
            rects2 = ax1.bar(x, sales_cogs, width, label='Cost of Goods (COGS)', color='#FFC107')
            rects3 = ax1.bar(x + width, general_expenses, width, label='Overhead Expenses', color='#F44336')
            
            # Only add bar labels if we have a reasonable number of bars
            if len(all_months) <= 12:   
                ax1.bar_label(rects1, padding=3, fmt='£%.2f', fontsize=8)
                ax1.bar_label(rects2, padding=3, fmt='£%.2f', fontsize=8)
                ax1.bar_label(rects3, padding=3, fmt='£%.2f', fontsize=8)

            ax1.set_ylabel("Amount (£)", color=FONT_COLOR)
            ax1.set_xticks(x)
            ax1.set_xticklabels(all_months, rotation=45, ha="right")
            ax1.set_title(plot_title, fontsize=14, fontweight='bold')
            ax1.grid(axis='y', linestyle='--', alpha=0.7)

            ax2 = ax1.twinx()
            ax2.plot(x, profit, color=PRIMARY_ACCENT, marker='o', linestyle='-', linewidth=2.5, label='Net Profit')
            ax2.set_ylabel("Net Profit (£)", color=PRIMARY_ACCENT, fontweight='bold')
            ax2.tick_params(axis='y', labelcolor=PRIMARY_ACCENT)
            ax2.axhline(0, color='grey', linestyle='--', linewidth=1)

            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

            fig.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)

        except Exception as e:
            messagebox.showerror("Chart Error", f"Could not plot profit chart: {e}")
            print(f"Chart plot error: {e}")


# ---------------- MAIN EXECUTION ----------------
if __name__ == "__main__":
    root = tk.Tk()
    app = FragranceManagerApp(root)
    root.mainloop() 