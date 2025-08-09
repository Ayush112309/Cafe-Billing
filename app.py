import functools
import sqlite3
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, session, g

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change this to a random, secure key in production
DB = 'cafe.db'

# Define the cafe menu with prices
MENU = {
    "Espresso": 2.50,
    "Latte": 3.00,
    "Cappuccino": 3.20,
    "ColdBrew": 3.50,
    "Coffee": 2.50,
    "Tea": 2.00,
    "Cake": 3.50,
    "Sandwich": 5.00,
    "Juice": 3.00,
    "Pasta": 6.00
}

def login_required(view):
    """Decorator to check if a user is logged in before allowing access to a view."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'username' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

def get_db():
    """Establishes a database connection."""
    if 'db' not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db():
    """Initializes the database tables if they don't exist."""
    with app.app_context():
        db = get_db()
        # Create users table for authentication
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                full_name TEXT
            )
        ''')
        # Create orders table with additional fields for customer and cashier
        db.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                customer_phone TEXT,
                cashier TEXT NOT NULL,
                items TEXT NOT NULL,
                total REAL NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        db.commit()

@app.teardown_appcontext
def close_db(e=None):
    """Closes the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.context_processor
def inject_globals():
    """Injects common variables into all templates."""
    return {
        'now': datetime.now,
        'current_user': session.get('username')
    }

@app.route("/")
@login_required
def index():
    """The landing page for a new order, prompting for customer details."""
    return render_template("index.html")

@app.route("/select_menu", methods=["POST"])
@login_required
def select_menu():
    """Handles customer details and displays the menu for ordering."""
    customer_name = request.form.get("customer_name")
    customer_phone = request.form.get("customer_phone")
    if not customer_name:
        flash("Customer name is required to start an order.", "warning")
        return redirect(url_for('index'))
    
    # Store customer details in session for the order
    session['customer_name'] = customer_name
    session['customer_phone'] = customer_phone

    return render_template("menu.html", menu=MENU, customer_name=customer_name)

@app.route("/submit_order", methods=["POST"])
@login_required
def submit_order():
    """Processes the menu order, saves it to the database, and shows the bill."""
    ordered = {}
    total = 0
    
    for item, price in MENU.items():
        try:
            qty = int(request.form.get(item, 0))
        except (ValueError, TypeError):
            qty = 0
        if qty > 0:
            ordered[item] = qty
            total += qty * price
    
    if not ordered:
        flash("Please select at least one item to order.", "warning")
        return redirect(url_for('index'))
    
    customer_name = session.get('customer_name')
    customer_phone = session.get('customer_phone')
    cashier = session.get('username')
    
    items_str = "; ".join(f"{item} x {qty}" for item, qty in ordered.items())
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db = get_db()
    db.execute(
        "INSERT INTO orders (customer_name, customer_phone, cashier, items, total, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (customer_name, customer_phone, cashier, items_str, total, ts)
    )
    db.commit()

    # Clear customer details from the session after the order is placed
    session.pop('customer_name', None)
    session.pop('customer_phone', None)
    
    flash("Order placed successfully!", "success")
    return render_template("bill.html", items=ordered, menu=MENU, total=total,
                           customer_name=customer_name, customer_phone=customer_phone, cashier=cashier)

@app.route("/report")
@login_required
def report():
    """Displays a sales report of all past orders."""
    db = get_db()
    rows = db.execute("SELECT * FROM orders ORDER BY timestamp DESC").fetchall()
    orders = [dict(row) for row in rows]
    return render_template("report.html", orders=orders)

@app.route("/register", methods=["GET", "POST"])
def register():
    """Handles user registration."""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        full_name = request.form.get("full_name")
        
        db = get_db()
        user_exists = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        
        if user_exists:
            flash("Username already exists.", "danger")
        else:
            db.execute("INSERT INTO users (username, password, full_name) VALUES (?, ?, ?)",
                       (username, password, full_name))
            db.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Handles user login and session management."""
    if 'username' in session:
        return redirect(url_for('index'))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ? AND password = ?",
                          (username, password)).fetchone()
        
        if user:
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            flash("Login successful!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password.", "danger")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    """Logs out the user and clears the session."""
    session.pop('username', None)
    session.pop('full_name', None)
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Initialize the database when the application starts
    init_db()
    # Run the application
    app.run(debug=True)
