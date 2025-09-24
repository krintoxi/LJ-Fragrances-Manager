LJ Fragrances Manager
A desktop application for managing fragrances, customers, and sales, built with Python 3, Tkinter, and SQLite. Ideal for small fragrance businesses looking to track inventory, customers, and sales efficiently.
Features

Fragrance Management
Add, edit, and delete fragrances
Supports images for each fragrance
Track unit cost, sale price, quantity, and inspired-by fragrances
Filter fragrances by gender (Men, Women, Unisex)
Low-stock alert (highlighted in red)

Customer Management
Add, edit, and delete customers
Track email, phone, city, and reference notes
Sales Tracking
Record sales for a fragrance and customer
Automatically updates fragrance quantity
Calculates revenue and profit per sale
Displays all sales in a dedicated tab
Search & Filter
Search fragrances by name or inspired fragrance
Easy navigation across tabs
Database
Local SQLite database

Fully self-contained: tables for fragrances, customers, and sales
Automatically creates database on first run

Installation
Clone the repository: git clone https://github.com/yourusername/lj-fragrances-manager.git
cd lj-fragrances-manager

Install dependencies:
pip install pillow

Tkinter is included with Python by default.

Run the app:

python3 main.py
On first run, the app will create fragrances.db automatically.

File Structure
lj-fragrances-manager/
│
├─ main.py             # Main Tkinter app
├─ database.py         # SQLite database functions
├─ assets/
│   └─ images/         # Fragrance images
└─ README.md           # Project documentation

Usage
Add Fragrance: Click "Add Fragrance", fill the details including gender and optional image, then save.
Edit/Delete Fragrance: Select a fragrance in the table and use the corresponding button.
Add Customer: Click "Add Customer" and fill out the details.
Record Sale: Select a fragrance, click "Record Sale", choose a customer or leave as walk-in, enter quantity, and save.
Search: Enter a name or inspired fragrance in the search bar to filter results.

Dependencies
Python 3.9+
Tkinter (built-in)
Pillow (for image support)
pip install pillow

Contributing
Fork the repository

Create a new branch: git checkout -b feature-name
Make changes and commit: git commit -m "Add feature"
Push to your branch: git push origin feature-name
Open a pull request
License
This project is licensed under the MIT License.
