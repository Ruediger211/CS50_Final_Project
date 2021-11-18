import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


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

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

# @app.route("/")
# @login_required
# def index():
#     """Show portfolio of stocks"""

#     # Collect data for table
#     user_id = session["user_id"]
#     portfolio = db.execute("SELECT symbol, SUM(number) AS n_shares FROM transactions WHERE user_id=? GROUP BY symbol", user_id)
#     grand_total = 0
#     for item in portfolio:
#         item['share_name'] = (lookup(item["symbol"]))["name"]
#         item['current_price'] = (lookup(item['symbol']))["price"]
#         item['total_value'] = item['current_price']*item['n_shares']
#         grand_total += item['total_value']
#         item['total_value'] = usd(item['total_value'])
#         item['current_price'] = usd(item['current_price'])
#     cash = db.execute("SELECT * FROM users WHERE id = ?", user_id)[0]['cash']
#     grand_total += cash
#     cash = usd(cash)
#     grand_total = usd(grand_total)
#     return render_template("index.html", portfolio=portfolio, cash=cash, grand_total=grand_total)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure symbol was submitted
        if not request.form.get("symbol"):
            return apology("must provide symbol", 400)

        # Ensure symbol does exist
        elif lookup(request.form.get("symbol")) == None:
            return apology("This symbol does not exist", 400)

        # Ensure number of shares was submitted
        elif not request.form.get("shares"):
            return apology("must provide number of shares", 400)

        # Ensure submitted number is numeric            https://www.w3schools.com/python/ref_string_isnumeric.asp
        elif not request.form.get("shares").isnumeric():
            return apology("number must be a positive integer", 400)

        # Collect transaction data and ensure that user has enough cash
        user_id = session["user_id"]
        symbol = request.form.get("symbol").upper()
        price = lookup(symbol)["price"]
        number = int(request.form.get("shares"))
        total = number * price
        cash = db.execute("SELECT * FROM users WHERE id = ?", user_id)[0]['cash']
        date_time = str(datetime.now())
        if total > cash:
            return apology("Sorry, not enough cash for this purchase")
        db.execute("INSERT INTO transactions (user_id, date_time, symbol, price, number, total) VALUES (?, ?, ?, ?, ?, ?)",
                user_id, date_time, symbol, price, number, total)
        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash-total, user_id)

        # Redirect user to login page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")


@app.route("/history", methods=["GET", "POST"])
@login_required
def history():

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        """Show history of transactions"""
        user_id = session["user_id"]
        start_date = request.form.get("start_date")
        transactions = db.execute("SELECT * FROM transactions WHERE user_id=user_id AND date_time >=?", start_date)
        for transaction in transactions:
            if transaction['number'] > 0:
                transaction['TType'] = "Purchase"
            else:
                transaction['TType'] = "Sale"
                transaction['number'] *= -1

        return render_template("history.html", transactions=transactions)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("start_date.html")


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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure symbol was submitted
        if not request.form.get("symbol"):
            return apology("must provide symbol", 400)

        # Ensure symbol does exist
        elif lookup(request.form.get("symbol")) == None:
            return apology("This symbol does not exist", 400)

        session["symbol"] = request.form.get("symbol").upper()
        return redirect("/quoted")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")


@app.route("/quoted")           # :( quote handles valid ticker symbol - expected to find "28.00" in page, but it wasn't found
@login_required                 # review session, look at IEX, download csv with stock data
def quoted():
    """Get stock quote."""

    return render_template("quoted.html", symbol=session["symbol"], name=lookup(session["symbol"])["name"], price=lookup(session["symbol"])["price"])


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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(rows) != 0:
            return apology("username allready in use", 400)

        username = request.form.get("username")
        password = request.form.get("password")
        hash = generate_password_hash(password)

        db.execute("INSERT INTO 'users' ('username', 'hash') VALUES (?, ?)", username, hash)

        # Redirect user to login page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure symbol was submitted
        if not request.form.get("symbol"):
            return apology("must provide symbol", 403)

        # Ensure user actually owns these shares
        own_shares = db.execute(
            "SELECT symbol, SUM(number) AS n_shares FROM transactions WHERE symbol=? GROUP BY symbol", request.form.get("symbol"))[0]['n_shares']
        if not own_shares:
            return apology("You do not own these shares", 403)
        if int(request.form.get("shares")) > own_shares:
            return apology("You do not have enough shares for this transaction")

        # Ensure number of shares was submitted and is a positive integer
        number = int(request.form.get("shares"))
        if not request.form.get("shares") or request.form.get("shares") != str(number) or number < 1:
            return apology("please provide a positive integer for the number of shares you want to sell", 403)

        # Collect transaction data and ensure that user has enough cash
        user_id = session["user_id"]
        symbol = request.form.get("symbol").upper()
        price = lookup(symbol)["price"]
        number = int(request.form.get("shares")) * -1
        total = number * price
        cash = db.execute("SELECT * FROM users WHERE id = ?", user_id)[0]['cash']
        date_time = str(datetime.now())
        db.execute("INSERT INTO transactions (user_id, date_time, symbol, price, number, total) VALUES (?, ?, ?, ?, ?, ?)",
                user_id, date_time, symbol, price, number, total)
        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash-total, user_id)

        # Redirect user to login page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)    # the options for the dropdown list have to be defined here.
    else:
        list_of_symbols = db.execute("SELECT DISTINCT symbol FROM transactions")
        return render_template("sell.html", list_of_symbols=list_of_symbols)


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
