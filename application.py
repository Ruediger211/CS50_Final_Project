import os

# from cs50 import SQL  --> not available outside cs50
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required#, lookup, usd
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import text


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Add Database
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///family.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

##### Custom filter
##### app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Initialize the Database
db = SQLAlchemy(app)

###### Make sure API key is set
#####if not os.environ.get("API_KEY"):
#####    raise RuntimeError("API_KEY not set")

@app.route("/")
@login_required
def index():
    # """Show portfolio of stocks"""

    # # Collect data for table
    # user_id = session["user_id"]
    # portfolio = db.execute("SELECT symbol, SUM(number) AS n_shares FROM transactions WHERE user_id=? GROUP BY symbol", user_id)
    # grand_total = 0
    # for item in portfolio:
    #     item['share_name'] = (lookup(item["symbol"]))["name"]
    #     item['current_price'] = (lookup(item['symbol']))["price"]
    #     item['total_value'] = item['current_price']*item['n_shares']
    #     grand_total += item['total_value']
    #     item['total_value'] = usd(item['total_value'])
    #     item['current_price'] = usd(item['current_price'])
    # cash = db.execute("SELECT * FROM users WHERE id = ?", user_id)[0]['cash']
    # grand_total += cash
    # cash = usd(cash)
    # grand_total = usd(grand_total)
    return render_template("index.html")


@app.route("/destinations")
@login_required
def destinations():

    """Show destinations"""
    destinations = db.execute("SELECT * FROM destinations")

    return render_template("destinations.html", destinations=destinations)


@app.route("/books", methods=["GET", "POST"])
@login_required
def books():

    """Show books"""
    books = db.execute("SELECT * FROM books")

    return render_template("books.html", books=books)


@app.route("/movies", methods=["GET", "POST"])
@login_required
def movies():

    """Show movies"""
    movies = db.execute("SELECT * FROM movies")

    return render_template("movies.html", movies=movies)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():

    #User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        name = request.form.get("destination")
        description = request.form.get("description")
        rating = request.form.get("rating")
        user_id = session["user_id"]
        db.execute("INSERT INTO destinations (dest_name, description, rating, user_id) VALUES (?, ?, ?, ?)", name, description, rating, user_id)
        return redirect("./destinations")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        list_destinations=db.execute("SELECT DISTINCT dest_name FROM destinations")
        return render_template("add.html", list_destinations=list_destinations)

@app.route("/top10")
@login_required
def top10():

    user_id = session["user_id"]
    tops = db.execute("SELECT dest_name, AVG(rating) AS avg FROM destinations GROUP BY dest_name ORDER BY AVG(rating) DESC")
    return render_template("top10.html", tops=tops)

    # #User reached route via POST (as by submitting a form via POST)
    # if request.method == "POST":
    #     name = request.form.get("destination")
    #     description = request.form.get("description")
    #     rating = request.form.get("rating")
    #     db.execute("INSERT INTO destinations (dest_name, description, rating) VALUES (?, ?, ?)", name, description, rating)
    #     return redirect("./destinations")

    # # User reached route via GET (as by clicking a link or via redirect)
    # else:
    #     return render_template("add.html")

# can be a template for checkings, then deleted.
# @app.route("/rating", methods=["GET", "POST"])
# @login_required
# def rating():

#     #User reached route via POST (as by submitting a form via POST)
#     if request.method == "POST":

#         # Ensure username was submitted
#         if not request.form.get("rating"):
#             return apology("must provide rating", 403)

#         # Ensure rating is an integer between 1 and 5
#         try:
#             input = int(request.form.get("rating"))
#         except:
#             input = 6
#         if input not in [1, 2, 3, 4, 5]:
#             return apology("please provide integer between 1 and 5", 403)

#         # # Query database for username
#         # rows = db.execute("SELECT * FROM family_members WHERE name = ?", request.form.get("username"))

#         # # Ensure username exists and password is correct
#         # if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
#         #     return apology("invalid username and/or password", 403)

#         # session["name"] = request.form.get("name")

#         # # Remember which user has logged in
#         # session["user_id"] = rows[0]["id"]

#         # Redirect user to home page
#         return redirect("/destinations")

#     # User reached route via GET (as by clicking a link or via redirect)
#     else:
#         return render_template("rating.html")



# @app.route("/...", methods=["GET", "POST"])

@app.route("/destination/<dest>")
@login_required
def destination(dest):
    destination = db.execute("SELECT family_members.name, destinations.description, destinations.dest_name FROM destinations JOIN family_members ON destinations.user_id = family_members.id WHERE dest_name =?", dest)
    return render_template("destination.html", destination=destination)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM family_members WHERE name = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["name"] = rows[0]["name"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide confirmation", 400)

        # Ensure password and confirmation are matching
        elif not (request.form.get("confirmation") == request.form.get("password")):
            return apology("Password and confirmation are not matching", 400)

        # Ensure username does not exist
        # Query database for username
        # rows = db.execute("SELECT * FROM family_members WHERE name = ?", request.form.get("username"))
        sql = text("SELECT * FROM family_members WHERE name = ?", request.form.get("username"))
        rows = db.engine.execute(sql)
        if len(rows) != 0:
            return apology("username allready in use", 400)

        username = request.form.get("username")
        password = request.form.get("password")
        hash = generate_password_hash(password)

        db.execute("INSERT INTO 'family_members' ('name', 'hash') VALUES (?, ?)", username, hash)

        # Redirect user to login page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


# Tools:

# print()
# print()
# print("****************************")
# print()
# print("symbol = ", symbol)
# print("lookup(symbol) = ", lookup(symbol))
# print()
# print("****************************")
# print()
