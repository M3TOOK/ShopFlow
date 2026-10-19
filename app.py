
import sqlite3
from flask import Flask, render_template, redirect, request

app = Flask(__name__)


# Database connection
def get_db():
    db = sqlite3.connect("app.db")
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


# Database initialization
def init_db():
    db = get_db()

    # Users (Customers)
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL
        )
    """)

    # Products
    db.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL CHECK (price > 0),
            quantity INTEGER NOT NULL CHECK (quantity >= 0),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)


    # Sales (Invoices)
    db.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total_amount REAL NOT NULL DEFAULT 0
                CHECK (total_amount >= 0),
            paid_amount REAL NOT NULL DEFAULT 0
                CHECK (paid_amount >= 0 AND paid_amount <= total_amount),
            date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)


    # Sale Items
    db.execute("""
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            price_per_unit REAL NOT NULL CHECK (price_per_unit > 0),
            FOREIGN KEY (sale_id) REFERENCES sales(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # Expenses
    db.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL CHECK (amount > 0),
            description TEXT NOT NULL,
            date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    db.commit()
    db.close()


# Dashboard
@app.route("/")
def dashboard():
    db = get_db()

    usersCount = db.execute(
        "SELECT COUNT(id) FROM users"
    ).fetchone()[0]

    users = db.execute("""
        SELECT id, username, phone
        FROM users
    """).fetchall()

    # Available balance = total sales - total expenses
    totalSales = db.execute("""
        SELECT COALESCE(SUM(si.quantity * si.price_per_unit), 0)
        FROM sale_items si
        JOIN sales s ON si.sale_id = s.id
    """).fetchone()[0]

    totalExpenses = db.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
    """).fetchone()[0]

    availableBalance = totalSales - totalExpenses

    db.close()

    return render_template(
        "dashboard.html",
        usersCount=usersCount,
        users=users,
        availableBalance=availableBalance
    )



@app.route("/products", methods=["GET", "POST"])
def products():
    db = get_db()
    error = None
    success = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price = request.form.get("price", type=float)
        quantity = request.form.get("quantity", type=int)

        if not name or price is None or quantity is None:
            error = "Please fill in all product fields."
        elif price <= 0:
            error = "Price must be greater than zero."
        elif quantity < 0:
            error = "Quantity cannot be negative."
        else:
            try:
                # مؤقتًا: استخدم أول مستخدم موجود بسبب user_id الإجباري في جدول products.
                owner = db.execute(
                    "SELECT id FROM users ORDER BY id LIMIT 1"
                ).fetchone()

                if owner is None:
                    error = "Create a user before adding products."
                else:
                    db.execute(
                        """
                        INSERT INTO products (user_id, name, price, quantity)
                        VALUES (?, ?, ?, ?)
                        """,
                        (owner["id"], name, price, quantity)
                    )
                    db.commit()
                    success = "Product added successfully."

            except sqlite3.IntegrityError:
                db.rollback()
                error = "Could not add this product."

    all_products = db.execute(
        """
        SELECT id, name, price, quantity
        FROM products
        ORDER BY id DESC
        """
    ).fetchall()

    db.close()

    return render_template(
        "products.html",
        products=all_products,
        error=error,
        success=success
    )



@app.route("/sales", methods=["GET", "POST"])
def sales():
    db = get_db()

    # Show the sale form
    if request.method == "GET":
        products = db.execute("""
            SELECT id, name, price, quantity
            FROM products
            ORDER BY name
        """).fetchall()

        db.close()
        return render_template("sales.html", products=products)

    try:
        # 1. Read form data
        customer_name = request.form.get("customer_name", "").strip()
        customer_phone = request.form.get("customer_phone", "").strip()
        product_id = request.form.get("product_id", type=int)
        quantity = request.form.get("quantity", type=int)
        paid_amount = request.form.get("paid_amount", type=float)

        if (
            not customer_name
            or not customer_phone
            or not product_id
            or quantity is None
            or quantity < 1
            or paid_amount is None
            or paid_amount < 0
        ):
            raise ValueError("Please enter valid sale information.")

        # 2. Get the selected product from the database
        product = db.execute("""
            SELECT id, name, price, quantity
            FROM products
            WHERE id = ?
        """, (product_id,)).fetchone()

        if product is None:
            raise ValueError("Product not found.")

        if quantity > product["quantity"]:
            raise ValueError("Not enough stock available.")

        # Always calculate using the database price
        total_amount = round(product["price"] * quantity, 2)

        if paid_amount > total_amount:
            raise ValueError("Paid amount cannot exceed total amount.")

        # 3. Find the customer by phone, or create a new one
        customer = db.execute("""
            SELECT id
            FROM users
            WHERE phone = ?
        """, (customer_phone,)).fetchone()

        if customer:
            customer_id = customer["id"]
        else:
            cursor = db.execute("""
                INSERT INTO users (username, phone)
                VALUES (?, ?)
            """, (customer_name, customer_phone))

            customer_id = cursor.lastrowid

        # 4. Create the invoice
        cursor = db.execute("""
            INSERT INTO sales (
                user_id, total_amount, paid_amount
            )
            VALUES (?, ?, ?)
        """, (customer_id, total_amount, paid_amount))

        sale_id = cursor.lastrowid

        # 5. Add the product to the invoice
        db.execute("""
            INSERT INTO sale_items (
                sale_id, product_id, quantity, price_per_unit
            )
            VALUES (?, ?, ?, ?)
        """, (
            sale_id,
            product_id,
            quantity,
            product["price"]
        ))

        # 6. Reduce inventory only if enough stock remains
        result = db.execute("""
            UPDATE products
            SET quantity = quantity - ?
            WHERE id = ? AND quantity >= ?
        """, (quantity, product_id, quantity))

        if result.rowcount != 1:
            raise ValueError("Stock changed. Please try again.")

        # Commit all changes together
        db.commit()

        return redirect("/sales")

    except (ValueError, TypeError) as error:
        db.rollback()

        products = db.execute("""
            SELECT id, name, price, quantity
            FROM products
            ORDER BY name
        """).fetchall()

        return render_template(
            "sales.html",
            products=products,
            error=str(error)
        ), 400

    except sqlite3.IntegrityError:
        db.rollback()

        products = db.execute("""
            SELECT id, name, price, quantity
            FROM products
            ORDER BY name
        """).fetchall()

        return render_template(
            "sales.html",
            products=products,
            error="Could not save the sale. Check the customer information."
        ), 400

    finally:
        db.close()


# History
@app.route("/history")
def history():
    return render_template("history.html")


# Initialize database tables
init_db()
