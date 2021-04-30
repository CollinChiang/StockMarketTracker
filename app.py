from flask import Flask, session, redirect
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import requests
from werkzeug.security import check_password_hash, generate_password_hash
from bs4 import BeautifulSoup
from functools import wraps


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = False

Session(app)

db = SQLAlchemy(app)


class User(db.Model):
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
        "price": s_price,
        "percent_increase": s_increase
    }

    return stock_data


def login_required(method):
    @wraps(method)
    def confirmation(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return method(*args, **kwargs)
    return confirmation


@app.route("/")
@login_required
def index():
    pass


@app.route("/login")
def login():
    pass


@app.route("/register")
def register():
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
