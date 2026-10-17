from flask import Flask,render_template

app = Flask(__name__)

@app.route("/")
def dashboard():
    return render_template("/dashboard.html")

@app.route("/products")
def products():
    return render_template("/products.html")

@app.route("/sales")
def sales():
    return render_template("/sales.html")

@app.route("/")
def history():
    return render_template("/history.html")

