from flask import Flask, session, redirect, render_template, request
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import requests
from werkzeug.security import check_password_hash, generate_password_hash
from bs4 import BeautifulSoup
from functools import wraps
import json
from string import ascii_letters, whitespace, punctuation
from tempfile import mkdtemp


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

Session(app)

db = SQLAlchemy(app)


class Users(db.Model):
    uuid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64))
    password = db.Column(db.String(256))
    stocks = db.Column(db.String(256))


def get_stock_data(symbol):
    url = f'https://finance.yahoo.com/quote/{symbol}/key-statistics?p={symbol}'

    data = requests.get(url)
    soup = BeautifulSoup(data.text, "html.parser")

    s_name = soup.find("h1", {"data-reactid": "7"}).text.strip()
    s_price = soup.find("span", {"data-reactid": "50"}).text.strip()
    s_increase = soup.find("span", {"data-reactid": "51"}).text.strip()

    stock_data = {
        "name": s_name,
        "symbol": symbol,
        "price": s_price,
        "percent_increase": s_increase
    }

    return stock_data


def login_required(method):
    @wraps(method)
    def confirmation(*args, **kwargs):
        if session.get("uuid") is None:
            return redirect("/login")
        return method(*args, **kwargs)
    return confirmation


def validate(string, arr):
    if string == "":
        return False

    for char in string:
        if char not in arr:
            return False
    return True


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@app.route("/")
@login_required
def index():
    query_users = Users.query.filter_by(uuid=session.get("uuid")).one()

    stocks = json.loads(query_users.stocks)

    stock_data = []
    for stock in stocks:
        stock_data.append(get_stock_data(stock))

    return render_template("index.html", stock_data=stock_data)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", data=None)
    elif request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()

        users_query = Users.query.filter_by(username=username)

        if users_query.count() > 0:
            for user in users_query:
                if check_password_hash(user.password, password):
                    session["uuid"] = user.uuid
                    return redirect("/")

        return render_template("login.html", message="Account information is invalid.")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()
        retype_password = request.form.get("retype_password").strip()

        if password != retype_password:
            return render_template("register.html", username=username, password=password, message="The confirmation password does not match your original password.")

        username_isvalid = validate(username, ascii_letters + whitespace)
        password_isvalid = validate(password, ascii_letters + whitespace + punctuation)

        if not username_isvalid and not password_isvalid:
            return render_template("register.html", username=username, password=password, message="The username and password contain invalid characters.")
        elif not username_isvalid:
            return render_template("register.html", username=username, password=password, message="The username contain invalid characters.")
        elif not password_isvalid:
            return render_template("register.html", username=username, password=password, message="The password contain invalid characters.")

        if Users.query.filter_by(username=username).count() != 0:
            return render_template("register.html", username=username, password=password, message="The username is already in use.")

        user = Users(username=username, password=generate_password_hash(password), stocks=json.dumps([]))
        db.session.add(user)
        db.session.commit()

        return redirect("/login")



@app.route("/add")
@login_required
def add():
    pass


@app.route("/remove")
@login_required
def remove():
    pass


def main():
    app.run()


if __name__ == '__main__':
    main()
