from flask import Flask, session, redirect, render_template, request
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import requests
from werkzeug.security import check_password_hash, generate_password_hash
from bs4 import BeautifulSoup
from functools import wraps
import json
from string import ascii_letters, whitespace, punctuation


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = False
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


def validate(str, arr):
    if str == "":
        return False

    for char in str:
        if char not in arr:
            return False
    return True


@app.route("/")
@login_required
def index():
    query_users = Users.query.filter_by(uuid=session.get("uuid")).one()

    stocks = json.loads(query_users.stocks)

    stock_data = []
    for stock in stocks:
        stock_data.append(get_stock_data(stock))

    render_template("index.html", stock_data=stock_data)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", data=None)
    elif request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()

        users_query = Users.query.filter_by(username=username, password=generate_password_hash(password))

        if users_query.count() != 1:
            return render_template("login.html", username=username, password=password, message="Account information is invalid.")

        session["uuid"] = users_query.uuid

        return redirect("/")


@app.route("/register")
def register():
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":
        pass


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
