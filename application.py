import os

# from cs50 import SQL  --> not available outside cs50
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import apology, login_required
from datetime import datetime
from peewee import *


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


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Initialize the Database
db = SqliteDatabase('family.db')
db.connect()


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/destinations")
@login_required
def destinations():

    """Show destinations"""
    cursor = db.execute_sql("SELECT * FROM destinations")
    destinations = cursor.fetchall()
    return render_template("destinations.html", destinations=destinations)


@app.route("/books", methods=["GET", "POST"])
@login_required
def books():

    """Show books"""
    books = db.execute_sql("SELECT * FROM books")

    return render_template("books.html", books=books)


@app.route("/movies", methods=["GET", "POST"])
@login_required
def movies():

    """Show movies"""
    movies = db.execute_sql("SELECT * FROM movies")

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
        db.execute_sql("INSERT INTO destinations (dest_name, description, rating, user_id) VALUES (?, ?, ?, ?)", (name, description, rating, user_id))
        return redirect("./destinations")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        list_destinations=db.execute_sql("SELECT DISTINCT dest_name FROM destinations")
        return render_template("add.html", list_destinations=list_destinations)

@app.route("/top10")
@login_required
def top10():

    user_id = session["user_id"]
    cursor = db.execute_sql("SELECT dest_name, AVG(rating) AS avg FROM destinations GROUP BY dest_name ORDER BY AVG(rating) DESC")
    tops = cursor.fetchall()
    return render_template("top10.html", tops=tops)

@app.route("/destination/<dest>")
@login_required
def destination(dest):
    cursor = db.execute_sql("SELECT family_members.name, destinations.description, destinations.dest_name FROM destinations JOIN family_members ON destinations.user_id = family_members.id WHERE dest_name =?", (dest,))
    destination = cursor.fetchall()
    print(destination) # returns tuple
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
        cursor = db.execute_sql("SELECT * FROM family_members WHERE name = ?", (request.form.get("username"),))
        rows = cursor.fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0][2], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # in the CS50 SQL module execute("SQL statement", username)
        # with peewee: execute_sql("SQL statement", (username,)), the username is in a tuple
        # a cursor is returned and to get a list, fetchall() has to be used. A list of tuples is returned
        # instead of a list of dictionaries!

        # Remember which user has logged in
        session["user_id"] = rows[0][0]
        session["name"] = rows[0][1]

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
        cursor = db.execute_sql("SELECT * FROM family_members WHERE name = ?", (request.form.get("username"),))
        rows = cursor.fetchall()
        if len(rows) != 0:
            return apology("username allready in use", 400)

        username = request.form.get("username")
        password = request.form.get("password")
        hash = generate_password_hash(password)

        db.execute_sql("INSERT INTO 'family_members' ('name', 'hash') VALUES (?, ?)", (username, hash))

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
