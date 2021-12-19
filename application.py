import os
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import apology, login_required
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.sql import text


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
app.config["SECRET_KEY"] = "f69-&HHt31;0kj6r?§dwWeEv"

DATABASE_URL = os.environ['DATABASE_URL'].replace('postgres://', 'postgresql://')

engine = create_engine(DATABASE_URL, echo=True) # on Heroku

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/destinations")
@login_required
def destinations():

    """Show destinations"""
    with engine.connect() as con:
        statement = text("""SELECT DISTINCT dest_name FROM destinations ORDER BY dest_name""")
        destinations = con.execute(statement)
    return render_template("destinations.html", destinations=destinations)

@app.route("/books")
@login_required
def books():

    """Show books"""
    with engine.connect() as con:
        statement = text("""SELECT DISTINCT book_name FROM books ORDER BY book_name""")
        books = con.execute(statement)
    return render_template("books.html", books=books)

@app.route("/movies")
@login_required
def movies():

    """Show movies"""
    with engine.connect() as con:
        statement = text("""SELECT DISTINCT movie_name FROM movies ORDER BY movie_name""")
        movies = con.execute(statement)
    return render_template("movies.html", movies=movies)

###############################################################################

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():

    #User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        name = request.form.get("destination")
        description = request.form.get("description")
        rating = request.form.get("rating")
        if rating not in ["1", "2", "3", "4", "5"]:
            return apology("Please choose an integer between 1 and 5", 400)
        user_id = session["user_id"]

        with engine.connect() as con:
            statement = text("SELECT * FROM destinations WHERE dest_name=:n AND user_id=:u").params(n=(request.form.get("username")), u=user_id)
            rows = con.execute(statement).fetchall()
        if len(rows) != 0:
            return apology("sorry, you allready rated this destination", 400)

        with engine.connect() as con:
            statement = text("INSERT INTO destinations (dest_name, description, rating, user_id) VALUES (:dn, :dsc, :rate, :uid)").params(dn=name, dsc=description, rate=rating, uid=user_id)
            con.execute(statement)
        return redirect("./destinations")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        with engine.connect() as con:
            statement = text("SELECT DISTINCT dest_name FROM destinations")
            list_destinations = con.execute(statement).fetchall()
        return render_template("add.html", list_destinations=list_destinations)

@app.route("/top10")
@login_required
def top10():

    user_id = session["user_id"]
    with engine.connect() as con:
        statement = text("SELECT dest_name, ROUND(AVG(rating), 1) AS avg FROM destinations GROUP BY dest_name ORDER BY AVG(rating) DESC")
        tops = con.execute(statement).fetchall()
    return render_template("top10.html", tops=tops)

@app.route("/destination/<item>")
@login_required
def destination(item):
    with engine.connect() as con:
            statement = text("SELECT users.name, destinations.description, destinations.dest_name, destinations.rating FROM destinations JOIN users ON destinations.user_id = users.id WHERE dest_name =:dn").params(dn=item)
            destination = con.execute(statement).fetchall()
    return render_template("destination.html", destination=destination)

################################################################################

@app.route("/add_book", methods=["GET", "POST"])
@login_required
def add_book():

    #User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        book = request.form.get("book")
        author = request.form.get("author")
        description = request.form.get("description")
        rating = request.form.get("rating")
        user_id = session["user_id"]
        with engine.connect() as con:
            statement = text("INSERT INTO books (book_name, author, description, rating, user_id) VALUES (:bn, :aut, :dsc, :rate, :uid)").params(bn=book, aut=author, dsc=description, rate=rating, uid=user_id)
            con.execute(statement)
        return redirect("./books")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        with engine.connect() as con:
            statement = text("SELECT DISTINCT book_name FROM books")
            list_books = con.execute(statement).fetchall()
        return render_template("add_book.html", list_books=list_books)

@app.route("/top10_books")
@login_required
def top10_books():

    user_id = session["user_id"]
    with engine.connect() as con:
        statement = text("SELECT book_name, ROUND(AVG(rating), 1) AS avg FROM books GROUP BY book_name ORDER BY AVG(rating) DESC")
        tops = con.execute(statement).fetchall()
    return render_template("top10_books.html", tops=tops)

@app.route("/book/<item>")
@login_required
def book(item):
    with engine.connect() as con:
            statement = text("SELECT users.name, books.description, books.book_name, books.rating FROM books JOIN users ON books.user_id = users.id WHERE book_name =:bn").params(bn=item)
            book = con.execute(statement).fetchall()
    return render_template("book.html", book=book)

################################################################################

@app.route("/add_movie", methods=["GET", "POST"])
@login_required
def add_movie():

    #User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        name = request.form.get("movie")
        description = request.form.get("description")
        rating = request.form.get("rating")
        user_id = session["user_id"]
        with engine.connect() as con:
            statement = text("INSERT INTO movies (movie_name, description, rating, user_id) VALUES (:mn, :dsc, :rate, :uid)").params(mn=name, dsc=description, rate=rating, uid=user_id)
            con.execute(statement)
        return redirect("./movies")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        with engine.connect() as con:
            statement = text("SELECT DISTINCT movie_name FROM movies")
            list_movies = con.execute(statement).fetchall()
        return render_template("add_movie.html", list_movies=list_movies)

@app.route("/top10_movies")
@login_required
def top10_movies():

    user_id = session["user_id"]
    with engine.connect() as con:
        statement = text("SELECT movie_name, ROUND(AVG(rating), 1) AS avg FROM movies GROUP BY movie_name ORDER BY AVG(rating) DESC")
        tops = con.execute(statement).fetchall()
    return render_template("top10_movies.html", tops=tops)

@app.route("/movie/<item>")
@login_required
def movie(item):
    with engine.connect() as con:
            statement = text("SELECT users.name, movies.description, movies.movie_name, movies.rating FROM movies JOIN users ON movies.user_id = users.id WHERE movie_name =:mn").params(mn=item)
            movie = con.execute(statement).fetchall()
    return render_template("movie.html", movie=movie)

################################################################################


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
        with engine.connect() as con:
            statement = text("SELECT * FROM users WHERE name=:name").params(name=(request.form.get("username")))
            rows = con.execute(statement).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0][2], request.form.get("password")):
            return apology("invalid username and/or password", 403)

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
        with engine.connect() as con:
            statement = text("SELECT * FROM users WHERE name=:n").params(n=(request.form.get("username")))
            rows = con.execute(statement).fetchall()
        if len(rows) != 0:
            return apology("username allready in use", 400)

        username = request.form.get("username")
        password = request.form.get("password")
        hash = generate_password_hash(password)
        with engine.connect() as con:
            statement = text("INSERT INTO users (name, hash) VALUES (:name, :hash)").params(name=username, hash=hash)
            con.execute(statement)

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
