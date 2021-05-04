from flask import Flask, session, redirect, render_template, request
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import requests
from bs4 import BeautifulSoup
from werkzeug.security import check_password_hash, generate_password_hash
from string import ascii_letters, whitespace, punctuation
import json
from functools import wraps
from tempfile import mkdtemp

# declare app as flask application
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.secret_key = b"J\x05{K\xbf$\x02oQ\t\xa2\xe3\x04*\x8a1\xdc\x81\x11\x1f\x17\xecZ("

# include flask as a session
Session(app)

# create database
db = SQLAlchemy(app)


class Users(db.Model):
    uuid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64))
    password = db.Column(db.String(256))
    stocks = db.Column(db.String(256))


def get_stock_data(symbol: str) -> dict:
    """This function uses bs4's BeautifulSoup to web-scrape the stock data from the yahoo finance stock page. The
    function will gather the data on the stock's name, symbol, price, and percent increase and will return that data in
    the form of a dictionary.

    :param symbol: str representing the stock's symbol
    :return: dict storing the stock's name, symbol, price, and percent increase
    """
    # generate url pointing to the stock symbol
    url = f'https://finance.yahoo.com/quote/{symbol}/key-statistics?p={symbol}'

    # retrieve data from the url by requests, then create a BeautifulSoup object with that request data
    data = requests.get(url)
    soup = BeautifulSoup(data.text, "html.parser")  # parse using html parser

    # retrieve the name, price, and percent increase of the stock
    s_name = soup.find("h1", {"data-reactid": "7"}).text.strip()
    s_price = soup.find("span", {"data-reactid": "50"}).text.strip()
    s_increase = soup.find("span", {"data-reactid": "51"}).text.strip()

    # format the name to leave out the (Stock Symbol)
    s_name = s_name[:len(s_name) - (len(symbol) + 2)]

    # create a dictionary storing the stock's data
    stock_data = {
        "name": s_name,
        "symbol": symbol,
        "price": s_price,
        "percent_increase": s_increase
    }

    # output the stock's data
    return stock_data


def validate(string: str, arr: list) -> bool:
    """This function takes in one string and an array of valid characters to validate the characters in the string. If
    a character in the string variable does not match any value within the array of valid characters, then validate will
    return False, signaling that the string variable contains illegal characters. If all characters in the string
    variable matches that of the valid character array list, then validate will return True.

    :param string: str representing value that needs to be validated
    :param arr: list representing all of the valid characters
    :return: bool if or if not the str contains valid characters
    """
    # invalidate empty strings
    if string == "":
        return False

    # invalidate if str value contains illegal characters
    for char in string:
        # detect invalid characters
        if char not in arr:
            return False
    return True


def login_required(method: any):
    """This function is a function wrapper that will make sure that all application pages that require a logged-in user
    force the user to first log in before continuing. The function works by checking if the session's uuid is not None,
    if it is None, then it redirects the user to the login function/page.

    :param method: this is what the function will wrap
    :return: a redirect or the method
    """
    # declare what happens wraps the method
    @wraps(method)
    def confirmation(*args, **kwargs):
        # sends user to the login page if the session does not have the user's uuid
        if session.get("uuid") is None:
            return redirect("/login")

        # otherwise, continue on with the method
        return method(*args, **kwargs)

    # continue on with the method
    return confirmation


@app.route("/")
@login_required
def index():
    """This function controls the homepage. It displays the index.html page and displays all stocks in the user's list
    of stocks. It shows the stock's symbol, name, price, and percent increase.

    :return: None
    """
    # query for the user's list of stocks
    stocks = json.loads(Users.query.filter_by(uuid=session["uuid"]).one().stocks)

    # store the stock data in a list
    stock_data = []
    for stock in stocks:
        # web-scrape stock data from yahoo finance stock page
        stock_data.append(get_stock_data(stock))

    # display the html page with the stock data
    return render_template("index.html", stocks=stock_data, stock_count=len(stocks))


@app.route("/login", methods=["GET", "POST"])
def login():
    """This function controls the login page. It displays the login.html page and takes in data from the login form. The
    function will validate the username and password by: checking if the username is already in the database and
    validating the password by comparing the hashing of the password. The request methods are GET and POST.

    :return: None
    """
    if request.method == "GET":
        # display the login.html page
        return render_template("login.html")

    elif request.method == "POST":
        # retrieve username and password
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()

        # query for user in database
        users_query = Users.query.filter_by(username=username)

        # validate password
        if users_query.count() > 0:
            # if there are more than 0 users, check all users for the correct username, password match
            for user in users_query:
                if check_password_hash(user.password, password):
                    # save session's uuid as the user's uuid
                    session["uuid"] = user.uuid

                    # send to the homepage
                    return redirect("/")

        # send invalid information message
        return render_template("login.html", message="Account information is invalid.")


@app.route("/register", methods=["GET", "POST"])
def register():
    """This function controls the register page. It displays the register.html page and takes in data from the register
    form. The function will validate the username and password by: validating that the confirmation password matches the
    original password, validating that the original password is not empty or contain illegal characters, validating that
    the username is not empty or contain illegal characters, and checking if the username does not already exists in the
    database. The request methods are GET and POST.

    :return: None
    """
    if request.method == "GET":
        # display the register.html page
        return render_template("register.html")

    elif request.method == "POST":
        # retrieve username, password, and the retyped password
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()
        retype_password = request.form.get("retype_password").strip()

        # validate that the original password matches the retyped password
        if password != retype_password:
            return render_template("register.html", username=username, password=password,
                                   message="The confirmation password does not match your original password.")

        # check username and password does not contain invalid characters
        username_isvalid = validate(username, ascii_letters + whitespace)
        password_isvalid = validate(password, ascii_letters + whitespace + punctuation)

        # validate username and password are correct and send back the appropriate message
        if not username_isvalid and not password_isvalid:
            return render_template("register.html", username=username, password=password,
                                   message="The username and password contain invalid characters.")
        elif not username_isvalid:
            return render_template("register.html", username=username, password=password,
                                   message="The username contain invalid characters.")
        elif not password_isvalid:
            return render_template("register.html", username=username, password=password,
                                   message="The password contain invalid characters.")

        # validate username is not already in database
        if Users.query.filter_by(username=username).count() != 0:
            return render_template("register.html", username=username, password=password,
                                   message="The username is already in use.")

        # add user to the users database
        user = Users(username=username, password=generate_password_hash(password), stocks=json.dumps([]))
        db.session.add(user)
        db.session.commit()

        # send to the login page
        return redirect("/login")


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """This function controls the add page. It displays the add.html page and takes data from the add form. The function
    will include a stock symbol to a user's list os tracked stocks if the stock is valid and is not already in the list
    of stocks. The function detects invalid stocks by attempting to retrieve the stock data and if a None Type attribute
    is returned, then the page the web-scraper is searching for is invalid. The function will save the stock into the
    user's list of stock if everything is valid.

    :return: None
    """
    if request.method == "GET":
        # display the add.html page
        return render_template("add.html")

    if request.method == "POST":
        # retrieve the stock symbol
        symbol = request.form.get("symbol").strip().upper()

        # validate stock page is there
        try:
            get_stock_data(symbol)

            # retrieve the user's list of stocks
            user = Users.query.filter_by(uuid=session["uuid"]).one()
            stocks = json.loads(user.stocks)

            # validate if the entered symbol is already in the user's list of stocks
            if symbol in stocks:
                return render_template("add.html", message=f"You are already tracking the stock: {symbol}.")

            # include the entered symbol into the list of stocks
            stocks.append(symbol)

            # save the new list of stocks into the database
            user.stocks = json.dumps(stocks)
            db.session.commit()

            # send to the homepage
            return redirect("/")

        # detect invalid stock page
        except AttributeError:
            return render_template("add.html", message="Stock symbol is not a valid symbol.")


@app.route("/remove", methods=["GET", "POST"])
@login_required
def remove():
    """This function controls the remove page. It displays the remove.html page and takes data from the remove form. The
    function will allow a user to remove a stock tracker from the homepage. It first takes in a stock symbol from the
    remove form, then removes the stock symbol from the user's list of stocks. If the stock symbol is not there (if the
    user did not choose a symbol to remove and kept it on the default symbol) then the application will detect the
    AttributeError and invalidate the symbol.

    :return: None
    """
    if request.method == "GET":
        # query for the user's list of stock symbols
        symbols = json.loads(Users.query.filter_by(uuid=session["uuid"]).one().stocks)

        # display the register.html page and render with the proper symbols
        return render_template("remove.html", symbols=symbols)

    elif request.method == "POST":
        # detect non-selected symbol with an AttributeError
        try:
            # retrieve the stock symbol
            symbol = request.form.get("symbol").strip()

        except AttributeError:
            # query for the user's list of stock symbols
            symbols = json.loads(Users.query.filter_by(uuid=session["uuid"]).one().stocks)

            # display the register.html with proper symbols and proper error message
            return render_template("remove.html", symbols=symbols, message="Please choose a symbol.")

        # query for the user's list of stocks
        query = Users.query.filter_by(uuid=session["uuid"]).one()
        stocks = json.loads(query.stocks)

        # remove the stock from the list of stocks
        stocks.remove(symbol)

        # save the updated list of stocks to the database
        query.stocks = json.dumps(stocks)
        db.session.commit()

        # send to the homepage
        return redirect("/")


@app.route("/logout")
@login_required
def logout():
    """This function logs the user out of their account. It just clears the session's uuid and moves the user back to
    the login page.

    :return: None
    """
    # clear the session's uuid
    session.pop("uuid", None)

    # send the user to the homepage (which then goes to the login page)
    return redirect("/")


if __name__ == '__main__':
    app.run()
