import os
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "shop.db")
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-development-secret")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL CHECK(price >= 0),
        image TEXT NOT NULL,
        stock INTEGER NOT NULL DEFAULT 20
    );
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        customer_name TEXT NOT NULL,
        address TEXT NOT NULL,
        total REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'Confirmed',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        product_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY(order_id) REFERENCES orders(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    );
    """)
    count = db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count == 0:
        products = [
            ("Classic Sneakers", "Comfortable everyday sneakers for casual wear.", "Fashion", 1499, "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=700", 20),
            ("Wireless Headphones", "Wireless headphones with clear sound and soft ear cushions.", "Electronics", 2299, "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=700", 15),
            ("Smart Watch", "A modern watch for notifications and daily activity.", "Electronics", 3199, "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=700", 12),
            ("Travel Backpack", "A practical backpack for college, work, and travel.", "Accessories", 1199, "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=700", 18),
            ("Cotton T-Shirt", "Soft cotton T-shirt for everyday comfort.", "Fashion", 599, "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=700", 30),
            ("Desk Lamp", "Minimal desk lamp for a study table or office.", "Home", 899, "https://images.unsplash.com/photo-150 и?w=700", 10),
            ("Sunglasses", "Lightweight sunglasses with a classic design.", "Accessories", 799, "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=700", 25),
            ("Coffee Mug", "Ceramic mug for coffee, tea, and other hot drinks.", "Home", 349, "https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?w=700", 40),
        ]
        # Replace a malformed sample URL with a valid generic image URL.
        products[5] = ("Desk Lamp", "Minimal desk lamp for a study table or office.", "Home", 899, "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=700", 10)
        db.executemany(
            "INSERT INTO products (name, description, category, price, image, stock) VALUES (?, ?, ?, ?, ?, ?)",
            products
        )
    db.commit()
    db.close()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "info")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def common_template_values():
    cart = session.get("cart", {})
    return {"cart_count": sum(int(q) for q in cart.values())}


@app.route("/")
def index():
    db = get_db()
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    sql = "SELECT * FROM products WHERE 1=1"
    params = []
    if search:
        sql += " AND (name LIKE ? OR description LIKE ? OR category LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])
    if category:
        sql += " AND category = ?"
        params.append(category)
    sql += " ORDER BY id DESC"
    products = db.execute(sql, params).fetchall()
    categories = db.execute("SELECT DISTINCT category FROM products ORDER BY category").fetchall()
    return render_template("index.html", products=products, categories=categories,
                           search=search, selected_category=category)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = get_db().execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if product is None:
        flash("Product not found.", "error")
        return redirect(url_for("index"))
    return render_template("product.html", product=product)


@app.post("/cart/add/<int:product_id>")
def add_to_cart(product_id):
    product = get_db().execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if product is None:
        flash("Product not found.", "error")
        return redirect(url_for("index"))
    cart = session.get("cart", {})
    key = str(product_id)
    current = int(cart.get(key, 0))
    if current >= product["stock"]:
        flash("Sorry, no more stock is available for this product.", "error")
    else:
        cart[key] = current + 1
        session["cart"] = cart
        flash(f"{product['name']} added to your cart.", "success")
    return redirect(request.referrer or url_for("index"))


@app.route("/cart")
def cart():
    db = get_db()
    cart_data = session.get("cart", {})
    items, total = [], 0
    for product_id, quantity in cart_data.items():
        product = db.execute("SELECT * FROM products WHERE id = ?", (int(product_id),)).fetchone()
        if product:
            quantity = int(quantity)
            subtotal = product["price"] * quantity
            items.append({"product": product, "quantity": quantity, "subtotal": subtotal})
            total += subtotal
    return render_template("cart.html", items=items, total=total)


@app.post("/cart/update/<int:product_id>")
def update_cart(product_id):
    cart = session.get("cart", {})
    key = str(product_id)
    quantity = request.form.get("quantity", "1", type=int)
    product = get_db().execute("SELECT stock FROM products WHERE id = ?", (product_id,)).fetchone()
    if key in cart:
        if quantity is None or quantity <= 0:
            cart.pop(key, None)
        elif product:
            cart[key] = min(quantity, product["stock"])
        session["cart"] = cart
    return redirect(url_for("cart"))


@app.post("/cart/remove/<int:product_id>")
def remove_from_cart(product_id):
    cart = session.get("cart", {})
    cart.pop(str(product_id), None)
    session["cart"] = cart
    flash("Item removed from cart.", "info")
    return redirect(url_for("cart"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your name and email, and use a password of at least 8 characters.", "error")
            return render_template("register.html")
        db = get_db()
        try:
            db.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                       (name, email, generate_password_hash(password)))
            db.commit()
        except sqlite3.IntegrityError:
            flash("That email is already registered. Please log in.", "error")
            return render_template("register.html")
        flash("Account created. You can now log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["cart"] = {}
            flash("Welcome back!", "success")
            return redirect(request.args.get("next") or url_for("index"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")


@app.post("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    db = get_db()
    cart_data = session.get("cart", {})
    items, total = [], 0
    for product_id, quantity in cart_data.items():
        product = db.execute("SELECT * FROM products WHERE id = ?", (int(product_id),)).fetchone()
        if product:
            quantity = int(quantity)
            subtotal = product["price"] * quantity
            items.append({"product": product, "quantity": quantity, "subtotal": subtotal})
            total += subtotal
    if not items:
        flash("Your cart is empty.", "info")
        return redirect(url_for("index"))
    if request.method == "POST":
        customer_name = request.form.get("customer_name", "").strip()
        address = request.form.get("address", "").strip()
        if not customer_name or not address:
            flash("Please enter your name and delivery address.", "error")
            return render_template("checkout.html", items=items, total=total)
        try:
            db.execute("BEGIN")
            for item in items:
                stock_row = db.execute("SELECT stock FROM products WHERE id = ?",
                                       (item["product"]["id"],)).fetchone()
                if not stock_row or stock_row["stock"] < item["quantity"]:
                    raise ValueError(f"Insufficient stock for {item['product']['name']}.")
            cursor = db.execute(
                "INSERT INTO orders (user_id, customer_name, address, total, status) VALUES (?, ?, ?, ?, ?)",
                (session["user_id"], customer_name, address, total, "Confirmed (demo payment)")
            )
            order_id = cursor.lastrowid
            for item in items:
                product = item["product"]
                db.execute(
                    "INSERT INTO order_items (order_id, product_id, product_name, quantity, price) VALUES (?, ?, ?, ?, ?)",
                    (order_id, product["id"], product["name"], item["quantity"], product["price"])
                )
                db.execute("UPDATE products SET stock = stock - ? WHERE id = ?",
                           (item["quantity"], product["id"]))
            db.commit()
        except (ValueError, sqlite3.Error) as exc:
            db.rollback()
            flash(str(exc) or "Could not place your order. Please try again.", "error")
            return redirect(url_for("cart"))
        session["cart"] = {}
        return redirect(url_for("order_confirmation", order_id=order_id))
    return render_template("checkout.html", items=items, total=total)


@app.route("/order/<int:order_id>")
@login_required
def order_confirmation(order_id):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?",
                       (order_id, session["user_id"])).fetchone()
    if not order:
        flash("Order not found.", "error")
        return redirect(url_for("my_orders"))
    items = db.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
    return render_template("order_confirmation.html", order=order, items=items)


@app.route("/my-orders")
@login_required
def my_orders():
    orders = get_db().execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", (session["user_id"],)
    ).fetchall()
    return render_template("my_orders.html", orders=orders)


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
