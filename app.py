
import sqlite3
from flask import Flask, render_template, redirect, request

app = Flask(__name__)


def get_db():
    db = sqlite3.connect("app.db")
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def init_db():
    db = get_db()

    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL CHECK (price > 0),
            quantity INTEGER NOT NULL CHECK (quantity >= 0)
        )
    """)

    columns = [
        row["name"]
        for row in db.execute("PRAGMA table_info(products)").fetchall()
    ]

    if "user_id" in columns:
        db.execute("PRAGMA foreign_keys = OFF")
        db.commit()

        try:
            db.execute("BEGIN")

            db.execute("""
                CREATE TABLE products_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL NOT NULL CHECK (price > 0),
                    quantity INTEGER NOT NULL CHECK (quantity >= 0)
                )
            """)

            db.execute("""
                INSERT INTO products_new (id, name, price, quantity)
                SELECT id, name, price, quantity FROM products
            """)

            db.execute("DROP TABLE products")
            db.execute("ALTER TABLE products_new RENAME TO products")
            db.commit()

        except Exception:
            db.rollback()
            raise

        finally:
            db.execute("PRAGMA foreign_keys = ON")

    db.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total_amount REAL NOT NULL DEFAULT 0
                CHECK (total_amount >= 0),
            paid_amount REAL NOT NULL DEFAULT 0
                CHECK (paid_amount >= 0 AND paid_amount <= total_amount),
            payment_method TEXT NOT NULL DEFAULT 'cash',
            date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    sales_columns = [
        row["name"]
        for row in db.execute("PRAGMA table_info(sales)").fetchall()
    ]

    if "payment_method" not in sales_columns:
        db.execute("""
            ALTER TABLE sales
            ADD COLUMN payment_method TEXT NOT NULL DEFAULT 'cash'
        """)

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


@app.route("/")
def dashboard():
    db = get_db()

    totalSales = db.execute("""
        SELECT COALESCE(SUM(total_amount), 0) FROM sales
    """).fetchone()[0]

    totalExpenses = db.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM expenses
    """).fetchone()[0]

    totalPaid = db.execute("""
        SELECT COALESCE(SUM(paid_amount), 0) FROM sales
    """).fetchone()[0]

    availableBalance = totalPaid - totalExpenses

    productsCount = db.execute("""
        SELECT COUNT(*) FROM products
    """).fetchone()[0]

    lowStockCount = db.execute("""
        SELECT COUNT(*) FROM products WHERE quantity <= 5
    """).fetchone()[0]

    recentSales = db.execute("""
        SELECT
            sales.id,
            sales.date,
            sales.total_amount,
            sales.paid_amount,
            users.username AS customer_name,
            users.phone AS customer_phone
        FROM sales
        JOIN users ON users.id = sales.user_id
        ORDER BY sales.id DESC
        LIMIT 5
    """).fetchall()

    pendingPayments = db.execute("""
    SELECT COALESCE(SUM(total_amount - paid_amount), 0)
    FROM sales
""").fetchone()[0]

    db.close()

    return render_template(
        "dashboard.html",
        totalSales=totalSales,
        availableBalance=availableBalance,
        productsCount=productsCount,
        lowStockCount=lowStockCount,
        recentSales=recentSales,
        pendingPayments=pendingPayments
    )


@app.route("/products", methods=["GET", "POST"])
def products():
    db = get_db()
    error = None
    success = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price = request.form.get("price", "").strip()
        quantity = request.form.get("quantity", "").strip()

        try:
            if not name:
                raise ValueError("Product name is required.")

            price = float(price)
            quantity = int(quantity)

            if price <= 0:
                raise ValueError("Price must be greater than zero.")

            if quantity < 0:
                raise ValueError("Quantity cannot be negative.")

            db.execute("""
                INSERT INTO products (name, price, quantity)
                VALUES (?, ?, ?)
            """, (name, price, quantity))

            db.commit()
            success = "Product added successfully."

        except (ValueError, TypeError):
            db.rollback()
            error = "Enter a valid name, price, and quantity."

    all_products = db.execute("""
        SELECT id, name, price, quantity
        FROM products
        ORDER BY id DESC
    """).fetchall()

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
    error = None

    if request.method == "POST":
        customer_name = request.form.get("customer_name", "").strip()
        customer_phone = request.form.get("customer_phone", "").strip()
        product_id = request.form.get("product_id", "").strip()
        quantity = request.form.get("quantity", "").strip()
        paid_amount = request.form.get("paid_amount", "").strip()
        payment_method = request.form.get("payment_method", "cash").strip()

        try:
            if not customer_name or not customer_phone:
                raise ValueError("Customer name and phone are required.")

            product_id = int(product_id)
            quantity = int(quantity)
            paid_amount = round(float(paid_amount), 2)

            if quantity <= 0:
                raise ValueError("Quantity must be greater than zero.")

            if paid_amount < 0:
                raise ValueError("Paid amount cannot be negative.")

            if payment_method not in ("cash", "card"):
                raise ValueError("Invalid payment method.")

            product = db.execute("""
                SELECT id, price, quantity
                FROM products
                WHERE id = ?
            """, (product_id,)).fetchone()

            if product is None:
                raise ValueError("Product not found.")

            if quantity > product["quantity"]:
                raise ValueError("Not enough stock available.")

            total_amount = round(product["price"] * quantity, 2)

            if paid_amount > total_amount:
                raise ValueError("Paid amount cannot exceed total amount.")

            customer = db.execute("""
                SELECT id FROM users WHERE phone = ?
            """, (customer_phone,)).fetchone()

            if customer:
                customer_id = customer["id"]

                db.execute("""
                    UPDATE users SET username = ? WHERE id = ?
                """, (customer_name, customer_id))
            else:
                db.execute("""
                    INSERT INTO users (username, phone)
                    VALUES (?, ?)
                """, (customer_name, customer_phone))

                customer_id = db.execute("""
                    SELECT id FROM users WHERE phone = ?
                """, (customer_phone,)).fetchone()["id"]

            cursor = db.execute("""
                INSERT INTO sales
                    (user_id, total_amount, paid_amount, payment_method)
                VALUES (?, ?, ?, ?)
            """, (
                customer_id,
                total_amount,
                paid_amount,
                payment_method
            ))

            sale_id = cursor.lastrowid

            db.execute("""
                INSERT INTO sale_items
                    (sale_id, product_id, quantity, price_per_unit)
                VALUES (?, ?, ?, ?)
            """, (
                sale_id,
                product_id,
                quantity,
                product["price"]
            ))

            result = db.execute("""
                UPDATE products
                SET quantity = quantity - ?
                WHERE id = ? AND quantity >= ?
            """, (quantity, product_id, quantity))

            if result.rowcount != 1:
                raise ValueError("Not enough stock available.")

            db.commit()
            db.close()

            return redirect("/sales")

        except (ValueError, TypeError, sqlite3.IntegrityError) as e:
            db.rollback()
            error = str(e) or "Unable to complete the sale."

    all_products = db.execute("""
        SELECT id, name, price, quantity
        FROM products
        ORDER BY name
    """).fetchall()

    db.close()

    return render_template(
        "sales.html",
        products=all_products,
        error=error
    ), 400 if error else 200


@app.route("/history")
def history():
    db = get_db()

    sales_history = db.execute("""
        SELECT
            sales.id,
            sales.date,
            sales.total_amount,
            sales.paid_amount,
            sales.payment_method,
            users.username AS customer_name,
            users.phone AS customer_phone
        FROM sales
        JOIN users ON users.id = sales.user_id
        ORDER BY sales.id DESC
    """).fetchall()

    db.close()

    return render_template(
        "history.html",
        sales=sales_history
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
