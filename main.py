import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
from datetime import datetime
from database import *

# Constants
UNIT_COST = 5.0
SALE_PRICE = 20.0
IMAGE_DIR = "assets/images/"

class FragranceManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LJ Fragrances Manager")
        self.root.geometry("1500x700")
        self.selected_image_path = None
        self.selected_id = None
        self.selected_customer_id = None
        self.image_cache = {}

        self.setup_ui()
        self.prefill_fragrances()

    def setup_ui(self):
        # Tabs
        self.tabControl = ttk.Notebook(self.root)
        self.men_tab = ttk.Frame(self.tabControl)
        self.women_tab = ttk.Frame(self.tabControl)
        self.unisex_tab = ttk.Frame(self.tabControl)
        self.customer_tab = ttk.Frame(self.tabControl)
        self.sales_tab = ttk.Frame(self.tabControl)

        self.tabControl.add(self.men_tab, text="Men")
        self.tabControl.add(self.women_tab, text="Women")
        self.tabControl.add(self.unisex_tab, text="Unisex")
        self.tabControl.add(self.customer_tab, text="Customers")
        self.tabControl.add(self.sales_tab, text="Sales")
        self.tabControl.pack(expand=1, fill="both")

        # Search bar
        search_frame = ttk.Frame(self.root)
        search_frame.pack(fill="x")
        ttk.Label(search_frame, text="Search by Name/Inspired By:").pack(side="left", padx=5)
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side="left", padx=5)
        ttk.Button(search_frame, text="Search", command=self.search_fragrance).pack(side="left", padx=5)
        ttk.Button(search_frame, text="Clear", command=self.refresh_all_tables).pack(side="left", padx=5)

        # Setup tables
        self.setup_fragrance_table(self.men_tab, "Men")
        self.setup_fragrance_table(self.women_tab, "Women")
        self.setup_fragrance_table(self.unisex_tab, "Unisex")
        self.setup_customer_table()
        self.setup_sales_table()

        # Buttons
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Add Fragrance", command=self.add_fragrance).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Edit Fragrance", command=self.edit_fragrance).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Delete Fragrance", command=self.delete_fragrance).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="Record Sale", command=self.record_sale).grid(row=0, column=3, padx=5)
        ttk.Button(btn_frame, text="Add Customer", command=self.add_customer).grid(row=0, column=4, padx=5)
        ttk.Button(btn_frame, text="Edit Customer", command=self.edit_customer).grid(row=0, column=5, padx=5)
        ttk.Button(btn_frame, text="Delete Customer", command=self.delete_customer).grid(row=0, column=6, padx=5)

    # --- Table Setup ---
    def setup_fragrance_table(self, parent, gender):
        columns = ("", "Name", "Inspired By", "Unit Cost", "Sale Price", "Quantity", "Total Cost", "Retail Value", "Gender")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")
        tree.pack(side="left", fill="both", expand=True)
        setattr(self, f"{gender.lower()}_tree", tree)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        tree.bind("<<TreeviewSelect>>", self.on_fragrance_select)
        self.populate_table(tree, gender)

    def setup_customer_table(self):
        columns = ("ID", "Name", "Email", "Phone", "City", "Reference")
        tree = ttk.Treeview(self.customer_tab, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        tree.pack(side="left", fill="both", expand=True)
        self.customer_tree = tree
        scrollbar = ttk.Scrollbar(self.customer_tab, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        tree.bind("<<TreeviewSelect>>", self.on_customer_select)
        self.populate_customers()

    def setup_sales_table(self):
        columns = ("ID", "Fragrance", "Customer", "Qty Sold", "Unit Cost", "Sale Price", "Revenue", "Profit", "Date")
        tree = ttk.Treeview(self.sales_tab, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(self.sales_tab, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.sales_tree = tree
        self.populate_sales()

    # --- Populate ---
    def populate_table(self, tree, gender):
        for row in tree.get_children():
            tree.delete(row)
        fragrances = get_all_fragrances_by_gender(gender)
        for f in fragrances:
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

            if f[9] and os.path.exists(f[9]):
                img = Image.open(f[9]).resize((50,50))
                photo = ImageTk.PhotoImage(img)
                self.image_cache[f[0]] = photo
            else:
                photo = None

            tags = ()
            if quantity < 5:
                tags=("low_stock",)

            tree.insert("", "end", iid=f[0],
                        values=(photo, f[1], f[7], unit_cost, sale_price, quantity, total_cost, retail_value, f[3]),
                        tags=tags)
        tree.tag_configure("low_stock", background="red")

    def populate_customers(self):
        for row in self.customer_tree.get_children():
            self.customer_tree.delete(row)
        for c in get_all_customers():
            self.customer_tree.insert("", "end", iid=c[0], values=c)

    def populate_sales(self):
        for row in self.sales_tree.get_children():
            self.sales_tree.delete(row)
        for s in get_all_sales():
            self.sales_tree.insert("", "end", iid=s[0], values=s)

    # --- Prefill ---
    def prefill_fragrances(self):
        prefill_list = [
            ("LJ Apex", "", "Men", "", UNIT_COST, SALE_PRICE, "Creed Aventus Absolute", 10, ""),
            ("LJ Alpha X", "", "Men", "", UNIT_COST, SALE_PRICE, "Creed Aventus", 10, ""),
            ("LJ Midnight Phantom", "", "Men", "", UNIT_COST, SALE_PRICE, "Bleu de Chanel Parfum", 10, ""),
            ("LJ Savage Apex", "", "Men", "", UNIT_COST, SALE_PRICE, "Dior Sauvage Elixir", 10, ""),
            ("LJ Ocean Prime", "", "Men", "", UNIT_COST, SALE_PRICE, "Giorgio Armani Acqua di Gio", 10, ""),
            ("LJ Titan Code", "", "Men", "", UNIT_COST, SALE_PRICE, "Jean Paul Gaultier", 10, ""),
            ("LJ Inferno Blast", "", "Men", "", UNIT_COST, SALE_PRICE, "Viktor & Rolf Spicebomb Extreme", 10, ""),
            ("LJ Gold Dominion", "", "Men", "", UNIT_COST, SALE_PRICE, "Paco Rabanne 1 Million", 10, ""),
            ("LJ Arctic Storm", "", "Men", "", UNIT_COST, SALE_PRICE, "Dolce & Gabbana Light Blue", 10, ""),
            ("LJ Voltage", "", "Men", "", UNIT_COST, SALE_PRICE, "Carolina Herrera Bad Boy", 10, ""),
            ("LJ Blackout X", "", "Men", "", UNIT_COST, SALE_PRICE, "Azzaro The Most Wanted", 10, ""),
            ("LJ Eros Fury", "", "Men", "", UNIT_COST, SALE_PRICE, "Versace Eros Energy", 10, ""),
            ("LJ Eros Inferno", "", "Men", "", UNIT_COST, SALE_PRICE, "Versace Eros", 10, ""),
            ("LJ Obsidian Woods", "", "Men", "", UNIT_COST, SALE_PRICE, "Le Labo Santal 33", 10, ""),
            ("LJ Shadow Diamond", "", "Men", "", UNIT_COST, SALE_PRICE, "Armani Black Carat Diamonds", 10, ""),
            ("LJ Silver Stratos", "", "Men", "", UNIT_COST, SALE_PRICE, "Creed Silver Mountain Water", 10, ""),
            ("LJ Monarch", "", "Men", "", UNIT_COST, SALE_PRICE, "Valentino Uomo", 10, ""),
            ("LJ Desert Mirage", "", "Men", "", UNIT_COST, SALE_PRICE, "Al-Rehab Golden Sand", 10, ""),
            ("LJ Elixir Prime", "", "Men", "", UNIT_COST, SALE_PRICE, "YSL Y Elixir", 10, ""),
            ("LJ Driftwood Noir", "", "Men", "", UNIT_COST, SALE_PRICE, "Caribbean Driftwood", 10, ""),
            ("LJ Celestial 540", "", "Women", "", UNIT_COST, SALE_PRICE, "Maison Francis Kurkdjian Baccarat Rouge 540", 10, ""),
            ("LJ Opulent Chic", "", "Women", "", UNIT_COST, SALE_PRICE, "Chanel Coco Mademoiselle", 10, ""),
            ("LJ Femme Fatalis", "", "Women", "", UNIT_COST, SALE_PRICE, "Carolina Herrera Good Girl", 10, ""),
            ("LJ Sugar Rush", "", "Women", "", UNIT_COST, SALE_PRICE, "Pink Sugar", 10, ""),
            ("LJ Velvet Ember", "", "Women", "", UNIT_COST, SALE_PRICE, "Prada Candy", 10, ""),
            ("LJ Empress Gold", "", "Women", "", UNIT_COST, SALE_PRICE, "YSL Libre", 10, ""),
            ("LJ Moonlight Rouge", "", "Women", "", UNIT_COST, SALE_PRICE, "Jimmy Choo I Want Choo", 10, ""),
            ("LJ Solar Essence", "", "Women", "", UNIT_COST, SALE_PRICE, "Mango Butter", 10, "")
        ]
        for f in prefill_list:
            if not get_fragrance_by_name(f[0]):
                insert_fragrance(f)
        self.refresh_all_tables()

    # --- Selection Handlers ---
    def on_fragrance_select(self, event):
        tree = event.widget
        selected = tree.selection()
        self.selected_id = int(selected[0]) if selected else None

    def on_customer_select(self, event):
        tree = event.widget
        selected = tree.selection()
        self.selected_customer_id = int(selected[0]) if selected else None

    # --- CRUD Operations ---
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
        delete_fragrance(self.selected_id)
        self.refresh_all_tables()
        self.selected_id = None

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

    # --- Forms ---
    def open_fragrance_form(self, edit=False):
        form = tk.Toplevel(self.root)
        form.title("Edit Fragrance" if edit else "Add Fragrance")
        form.geometry("500x500")
        labels = ["Name","Description","Gender","Barcode","Unit Cost","Sale Price","Inspired By","Quantity"]
        entries = []
        gender_var = tk.StringVar()
        for i, label in enumerate(labels):
            ttk.Label(form, text=label).grid(row=i, column=0, padx=5, pady=5, sticky="w")
            if label == "Gender":
                combo = ttk.Combobox(form, textvariable=gender_var, values=["Men","Women","Unisex"], state="readonly")
                combo.grid(row=i, column=1, padx=5, pady=5)
                entries.append(gender_var)
            else:
                e = ttk.Entry(form)
                e.grid(row=i, column=1, padx=5, pady=5)
                entries.append(e)

        # Image upload
        def upload_image():
            path = filedialog.askopenfilename(filetypes=[("Image files","*.png;*.jpg;*.jpeg")])
            if path:
                self.selected_image_path = path
                ttk.Label(form, text=f"Image: {os.path.basename(path)}").grid(row=8, column=1, sticky="w")
        ttk.Button(form, text="Upload Image", command=upload_image).grid(row=8, column=0, padx=5, pady=5)

        # Pre-fill if editing
        if edit:
            f = get_fragrance_by_id(self.selected_id)
            entries[0].insert(0, f[1])
            entries[1].insert(0, f[2])
            entries[2].set(f[3])
            entries[3].insert(0, f[4])
            entries[4].insert(0, str(f[5]))
            entries[5].insert(0, str(f[6]))
            entries[6].insert(0, f[7])
            entries[7].insert(0, str(f[8]))
            self.selected_image_path = f[9]

        def save():
            try:
                name = entries[0].get()
                description = entries[1].get()
                gender = entries[2].get()
                barcode = entries[3].get()
                unit_cost = float(entries[4].get())
                sale_price = float(entries[5].get())
                inspired_by = entries[6].get()
                quantity = int(entries[7].get())
            except:
                messagebox.showerror("Error","Unit Cost, Sale Price, Quantity must be numeric")
                return
            data = (name, description, gender, barcode, unit_cost, sale_price, inspired_by, quantity, self.selected_image_path)
            if edit:
                update_fragrance(self.selected_id, data)
            else:
                insert_fragrance(data)
            self.selected_image_path = None
            form.destroy()
            self.refresh_all_tables()

        ttk.Button(form, text="Save", command=save).grid(row=9, column=1, pady=10)

    def open_customer_form(self, edit=False):
        form = tk.Toplevel(self.root)
        form.title("Edit Customer" if edit else "Add Customer")
        form.geometry("400x400")
        labels = ["Name","Email","Phone","City","Reference"]
        entries = []
        for i, label in enumerate(labels):
            ttk.Label(form, text=label).grid(row=i, column=0, padx=5, pady=5, sticky="w")
            e = ttk.Entry(form)
            e.grid(row=i, column=1, padx=5, pady=5)
            entries.append(e)

        if edit:
            c = get_customer_by_id(self.selected_customer_id)
            for idx, e in enumerate(entries):
                e.insert(0, c[idx+1])

        def save():
            data = [e.get() for e in entries]
            if edit:
                update_customer(self.selected_customer_id, data)
            else:
                insert_customer(data)
            form.destroy()
            self.populate_customers()

        ttk.Button(form, text="Save", command=save).grid(row=6, column=1, pady=10)

    # --- Sales ---
    def record_sale(self):
        if not self.selected_id:
            messagebox.showwarning("No Selection","Select fragrance to sell")
            return
        form = tk.Toplevel(self.root)
        form.title("Record Sale")
        form.geometry("400x300")

        ttk.Label(form, text="Customer:").grid(row=0, column=0, padx=5, pady=5)
        customers = [f"{c[1]} (ID:{c[0]})" for c in get_all_customers()]
        customer_var = tk.StringVar()
        cust_combo = ttk.Combobox(form, values=customers, textvariable=customer_var, state="readonly")
        cust_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Quantity:").grid(row=1, column=0, padx=5, pady=5)
        qty_entry = ttk.Entry(form)
        qty_entry.grid(row=1, column=1, padx=5, pady=5)

        def save_sale():
            customer_selection = cust_combo.get()
            if not customer_selection:
                messagebox.showerror("Error","Select a customer")
                return
            try:
                qty = int(qty_entry.get())
                if qty <=0:
                    raise ValueError
            except:
                messagebox.showerror("Error","Enter a valid quantity")
                return

            customer_id = int(customer_selection.split("ID:")[1].replace(")",""))
            fragrance = get_fragrance_by_id(self.selected_id)
            if fragrance[8] < qty:
                messagebox.showerror("Error","Not enough stock")
                return
            unit_cost = float(fragrance[5])
            sale_price = float(fragrance[6])
            revenue = sale_price * qty
            profit = revenue - (unit_cost * qty)
            sale_data = (self.selected_id, customer_id, qty, unit_cost, sale_price, revenue, profit, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            insert_sale(sale_data)
            update_fragrance_quantity(self.selected_id, fragrance[8]-qty)
            form.destroy()
            self.refresh_all_tables()
            self.populate_sales()

        ttk.Button(form, text="Save Sale", command=save_sale).grid(row=2, column=1, pady=10)

    # --- Helpers ---
    def refresh_all_tables(self):
        self.populate_table(self.men_tree,"Men")
        self.populate_table(self.women_tree,"Women")
        self.populate_table(self.unisex_tree,"Unisex")
        self.populate_customers()
        self.populate_sales()

    def search_fragrance(self):
        query = self.search_entry.get().lower()
        if not query:
            self.refresh_all_tables()
            return
        for gender, tree in [("Men",self.men_tree),("Women",self.women_tree),("Unisex",self.unisex_tree)]:
            for row in tree.get_children():
                tree.delete(row)
            fragrances = get_all_fragrances_by_gender(gender)
            for f in fragrances:
                if query in f[1].lower() or query in f[7].lower():
                    tree.insert("", "end", iid=f[0], values=(f[1], f[7], f[3], f[5], f[6], f[8]))

if __name__=="__main__":
    root = tk.Tk()
    app = FragranceManagerApp(root)
    root.mainloop()
