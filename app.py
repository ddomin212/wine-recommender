# write the usual flask imports
import contextlib
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
)
from flask_session import Session
from redis import Redis
from fbc import config
from functions.model import predict_hf
import pickle
import os
import pyrebase
import json
import asyncio

# write the usual flask app setup
app = Flask(__name__)
if os.getenv("PROD") != "true":
    from dotenv import load_dotenv

    load_dotenv()
app.secret_key = os.getenv("APP_SECRET_KEY")
# configure the session to use redis
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_REDIS"] = Redis(
    host="redis-10870.c55.eu-central-1-1.ec2.cloud.redislabs.com",
    port=10870,
    password=os.getenv("REDIS_PASSWORD"),
)
Session(app)
# connect to firebase authentication and realtime database
firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()
ind = pickle.load(open("static/data/index.pkl", "rb"))
# write an api that accepts a text input on post and just renders on get


@app.route("/api", methods=["POST"])
def api():
    x = json.loads(request.data)
    val = x["text"]
    pred = asyncio.run(predict_hf(val))
    with contextlib.suppress(KeyError):
        db.child("query").push(
            {"user": session["user"], "query": val, "prediction": pred}
        )
    return jsonify({"prediction": pred})


@app.route("/", methods=["GET", "POST"])
def index():
    image_url = url_for("static", filename="img/hero.webp")
    with contextlib.suppress(KeyError):
        user = session["user"]
        user = auth.refresh(user["refreshToken"])
    return render_template("index.html", image_url=image_url)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            session["user"] = user
            return redirect(url_for("index"))
        except Exception:
            return "Invalid email or password", 401

    image_url = url_for("static", filename="img/wine.jpg")
    return render_template("login.html", image_url=image_url)


# write a logout page


@app.route("/logout")
def logout():
    session.pop("user", None)
    # auth.current_user = None
    return redirect(url_for("login"))


# write a signup page that accepts a text input on post and just renders on get


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        try:
            auth.create_user_with_email_and_password(email, password)
            return redirect(url_for("login"))
        except Exception:
            return "Invalid email or password", 401
    image_url = url_for("static", filename="img/wineyard.jpg")
    return render_template("login.html", mode="signup", image_url=image_url)


# write a history page that renders all the data for a current user from the "queries" table


@app.route("/history")
def history():
    user_info = session["user"]
    all_querys = db.child("query").get()
    queries = [
        query.val()
        for query in all_querys.each()
        if query.val().get("user").get("email") == user_info["email"]
    ]
    return render_template("history.html", queries=queries)


# run flask in main
if __name__ == "__main__":
    app.run(debug=True)
