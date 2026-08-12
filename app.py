from flask import Flask, render_template, session, redirect, url_for, request
from database import get_db_connection
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")


# =================================
# HOME PAGE
# =================================

@app.route("/")
def home():

    search = request.args.get("search", "")

    category = request.args.get("category", "")

    connection = get_db_connection()

    cursor = connection.cursor(dictionary=True)


    # Get all categories

    cursor.execute(
        "SELECT DISTINCT category FROM products"
    )

    categories = cursor.fetchall()


    # Search and category filter

    query = "SELECT * FROM products WHERE 1=1"

    values = []


    if search:

        query += " AND name LIKE %s"

        values.append("%" + search + "%")


    if category:

        query += " AND category = %s"

        values.append(category)


    cursor.execute(query, values)

    products = cursor.fetchall()


    cursor.close()

    connection.close()


    return render_template(
        "index.html",
        products=products,
        categories=categories,
        search=search,
        selected_category=category
    )


# =================================
# PRODUCT DETAILS
# =================================

@app.route("/product/<int:product_id>")
def product_details(product_id):

    connection = get_db_connection()

    cursor = connection.cursor(dictionary=True)


    cursor.execute(
        "SELECT * FROM products WHERE id = %s",
        (product_id,)
    )

    product = cursor.fetchone()


    cursor.close()

    connection.close()


    if product is None:

        return "Product not found", 404


    return render_template(
        "product.html",
        product=product
    )


# =================================
# ADD TO CART
# =================================

@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):

    cart = session.get("cart", {})


    product_id = str(product_id)


    if product_id in cart:

        cart[product_id] += 1

    else:

        cart[product_id] = 1


    session["cart"] = cart


    return redirect(url_for("home"))


# =================================
# CART PAGE
# =================================

@app.route("/cart")
def cart():

    cart = session.get("cart", {})


    # Clear old cart data if it is a list

    if isinstance(cart, list):

        cart = {}

        session["cart"] = cart


    products = []

    total = 0


    connection = get_db_connection()

    cursor = connection.cursor(dictionary=True)


    for product_id, quantity in cart.items():

        cursor.execute(
            "SELECT * FROM products WHERE id = %s",
            (product_id,)
        )


        product = cursor.fetchone()


        if product:

            product["quantity"] = quantity

            product["subtotal"] = (
                float(product["price"]) * quantity
            )


            total += product["subtotal"]

            products.append(product)


    cursor.close()

    connection.close()


    return render_template(
        "cart.html",
        products=products,
        total=total
    )


# =================================
# INCREASE QUANTITY
# =================================

@app.route("/increase/<int:product_id>")
def increase(product_id):

    cart = session.get("cart", {})


    product_id = str(product_id)


    if product_id in cart:

        cart[product_id] += 1


    session["cart"] = cart


    return redirect(url_for("cart"))


# =================================
# DECREASE QUANTITY
# =================================

@app.route("/decrease/<int:product_id>")
def decrease(product_id):

    cart = session.get("cart", {})


    product_id = str(product_id)


    if product_id in cart:

        cart[product_id] -= 1


        if cart[product_id] <= 0:

            del cart[product_id]


    session["cart"] = cart


    return redirect(url_for("cart"))


# =================================
# REMOVE FROM CART
# =================================

@app.route("/remove_from_cart/<int:product_id>")
def remove_from_cart(product_id):

    cart = session.get("cart", {})


    product_id = str(product_id)


    if product_id in cart:

        del cart[product_id]


    session["cart"] = cart


    return redirect(url_for("cart"))


# =================================
# REGISTER
# =================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]

        email = request.form["email"]

        password = request.form["password"]


        connection = get_db_connection()

        cursor = connection.cursor()


        query = """
        INSERT INTO users (name, email, password)
        VALUES (%s, %s, %s)
        """


        cursor.execute(
            query,
            (name, email, password)
        )


        connection.commit()


        cursor.close()

        connection.close()


        return redirect(url_for("login"))


    return render_template("register.html")


# =================================
# LOGIN
# =================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]


        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)


        query = """
        SELECT * FROM users
        WHERE email = %s AND password = %s
        """


        cursor.execute(
            query,
            (email, password)
        )


        user = cursor.fetchone()


        cursor.close()

        connection.close()


        if user:

            session["user_id"] = user["id"]

            session["user_name"] = user["name"]


            return redirect(url_for("home"))


        else:

            return render_template(
                "login.html",
                error="Invalid email or password"
            )


    return render_template("login.html")


# =================================
# LOGOUT
# =================================

@app.route("/logout")
def logout():

    session.pop("user_id", None)

    session.pop("user_name", None)


    return redirect(url_for("home"))


# =================================
# CHECKOUT
# =================================

@app.route("/checkout", methods=["GET", "POST"])
def checkout():

    cart = session.get("cart", {})


    # If cart is empty

    if not cart:

        return redirect(url_for("cart"))


    total = 0


    connection = get_db_connection()

    cursor = connection.cursor(dictionary=True)


    # Calculate total

    for product_id, quantity in cart.items():

        cursor.execute(
            "SELECT * FROM products WHERE id = %s",
            (product_id,)
        )


        product = cursor.fetchone()


        if product:

            total += (
                float(product["price"]) * quantity
            )


    cursor.close()

    connection.close()


    # Show checkout page

    if request.method == "GET":

        return render_template(
            "checkout.html",
            total=total
        )


    # Place order

    if request.method == "POST":

        name = request.form["name"]

        email = request.form["email"]

        phone = request.form["phone"]

        address = request.form["address"]


        # Clear cart

        session["cart"] = {}


        return render_template(
            "order_success.html",
            name=name,
            total=total
        )


# =================================
# RUN FLASK
# =================================

if __name__ == "__main__":

    app.run(debug=True)