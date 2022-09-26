from flask import Flask, render_template, session, abort, send_from_directory, redirect, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, login_required, logout_user, UserMixin
from zenora import APIClient, User, UserAPI
import os
from dotenv import load_dotenv
import requests
from functools import wraps

load_dotenv()

app = Flask(__name__)
client = APIClient(os.getenv("TOKEN"), client_secret=os.getenv("CLIENT_SECRET"))

TEAM = []

app.config["SECRET_KEY"] = "..."
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"

db = SQLAlchemy(app)

def admin_ensure(func):

    @wraps(func)
    def predicate(*args, **kwargs):
        if current_user.id in TEAM:
            return func(*args, **kwargs)
        return abort(403)
    return predicate

class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    bio = db.Column(db.String(150))

loginManager = LoginManager(app)

@loginManager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.errorhandler(401)
def unauthorized(e=None):
    return render_template("unauthorized.html", current_user=current_user, discord=get_discord())

@app.errorhandler(403)
def unauthorized(e=None):
    return render_template("forbidden.html", current_user=current_user, discord=get_discord())

@app.errorhandler(404)
def unauthorized(e=None):
    return render_template("notFound.html", current_user=current_user, discord=get_discord())



@app.route("/login")
def login():
    if current_user.is_authenticated:
        return redirect("/profile")
    else:
        return redirect(os.getenv("OAUTH_URL"))

class Bot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner = db.Column(db.Integer)
    short = db.Column(db.String(200))
    long = db.Column(db.String(10000))
    prefix = db.Column(db.String(200))    
    invlink = db.Column(db.String(200))
    image_link = db.Column(db.String(200))  
    avatar_url = db.Column(db.String(400))
    name = db.Column(db.String(60))
    vote_count = db.Column(db.Integer, default=0, nullable=True)
    approved = db.Column(db.Integer, default=0, nullable=True)


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bot = db.Column(db.Integer)
    rating = db.Column(db.Integer)
    text = db.Column(db.String(150))
    owner = db.Column(db.String(150))

@app.route("/api/callback")
def callback():
    code = request.args.get("code")
    resp = client.oauth.get_access_token(code, os.getenv("REDIRECT_URI"))
    bearer_client = APIClient(resp.access_token, bearer=True)
    currentUser = bearer_client.users.get_current_user()
    if User.query.filter_by(id=currentUser.id).first():
        u = User.query.filter_by(id=currentUser.id).first()
        login_user(u)
    else:
        u = User(id=currentUser.id, bio="Hey there!")
        db.session.add(u)
        db.session.commit()
        login_user(u)
    session["USER"] = {
        "name": currentUser.username,
        "id": currentUser.id,
        "avatar_url": currentUser.avatar_url,
        "accent_color": currentUser.accent_color,
        "discriminator": currentUser.discriminator,
    }
    return render_template("redirecting.html", current_user=current_user, discord=get_discord(), cstr="You are being logged in...", to="/")

@app.route("/api/current_user/<attr>")
@login_required
def currentuser_attr(attr):
    return session["USER"].get(attr)

@app.route("/api/current_user/av")
@login_required
def currentuser_avt():
    avatar = session["USER"].get("avatar_url")
    r = requests.get(avatar)
    return r.content

@app.route("/sl-backend/sl-addbot.dhp", methods=["POST"])
@login_required
def add_bot():
    bot_id = request.form["botID"]
    short = request.form["shortDsc"]
    long = request.form["long"]
    image = request.form.get("imglink")
    prefix = request.form["prefix"]
    invite = request.form["invite"]
    r = requests.get(f"https://japi.rest/discord/v1/application/{bot_id}")
    if "message" in r.text:
        return abort(401)
    print(r.json())
        
    bot = Bot(id=bot_id, owner=current_user.id, short=short, long=long, prefix=prefix, invlink=invite, image_link=image, avatar_url=r.json()["data"]["bot"]["avatarURL"], name=r.json()["data"]["application"]["name"])
    db.session.add(bot)
    db.session.commit()
    return render_template("success.html", current_user=current_user, discord=get_discord(),bot=bot)

@app.route("/search")
def search():
    query = request.args.get("query")
    bots = Bot.query.filter(Bot.name.like(f"%{query}%"), Bot.approved.like(0)).all()
    
    return render_template("list.html", current_user=current_user, discord=get_discord(),bots=bots)

@app.route("/admin/panel")
@login_required
@admin_ensure
def panel():
    bots = Bot.query.filter_by(approved=0).all()
    return render_template("panel.html", current_user=current_user, discord=get_discord(),bots=bots)

@app.route("/admin/bot/<id>")
@login_required
@admin_ensure
def panel_bot(id):
    bot = Bot.query.get(id)
    reviews = Review.query.filter_by(bot=bot.id).all()
    num = 0
    for r in reviews:
        num += r.rating
    if len(reviews) > 0:
        num /= len(reviews)
    else: num = 0
    return render_template("staffbot.html", current_user=current_user, discord=get_discord(),bot=bot, VOTEAVRG=num, reviews=reviews)

@app.route("/bot/<id>")
@login_required
def bot(id):
    bot = Bot.query.get(id)
    reviews = Review.query.filter_by(bot=bot.id).all()
    num = 0
    for r in reviews:
        num += r.rating
    if len(reviews) > 0:
        num /= len(reviews)
    else: num = 0
    return render_template("bot.html", current_user=current_user, discord=get_discord(),bot=bot, VOTEAVRG=num, reviews=reviews)


@app.route("/bot/<id>/vote")
@login_required
def bot_vote(id):
    bot = Bot.query.get(id)
    reviews = Review.query.filter_by(bot=bot.id).all()
    num = 0
    for r in reviews:
        num += r.rating
    if len(reviews) > 0:
        num /= len(reviews)
    else: num = 0
    return render_template("redirecting.html", current_user=current_user, discord=get_discord(), cstr="Error, Not Implemented yet! Redirecting...", to=f"/bot/{id}")


@app.route("/admin/bot/<id>/decision")
@login_required
@admin_ensure
def bot_decide(id):
    bot = Bot.query.get(id)
    return render_template("decision.html", current_user=current_user, discord=get_discord(),bot=bot)

@app.route("/admin/bot/<id>/approve")
@login_required
@admin_ensure
def bot_approve(id):
    bot = Bot.query.get(id)
    bot.approved = True
    db.session.commit()
    return render_template("redirecting.html", current_user=current_user, discord=get_discord(), cstr="Bot Approved! Redirecting...", to="/admin/panel")


@app.route("/admin/bot/<id>/decline")
@login_required
@admin_ensure
def bot_decline(id):
    bot = Bot.query.get(id)
    db.session.delete(bot)
    db.session.commit()
    reason = request.form["reason"]
    return render_template("redirecting.html", current_user=current_user, discord=get_discord(), cstr="Bot Declined! Redirecting...", to="/admin/panel")

@app.before_request
def before_request():
    if not "USER" in session:
        session["USER"] = {}
    return

@app.route("/logoff")
@login_required
def logoff():
    logout_user()
    return render_template("redirecting.html", current_user=current_user, discord=get_discord(), cstr="Redirecting...", to="/")
    
@app.route("/user/<id>")
def user_by(id):
    u: User = User.query.get(id)
    if not u:
        abort(404)
    class U:
        def __init__(self, **vars):
            for k, v in vars.items():
                setattr(self, k, v)

    r = requests.get(f"https://api.discord.name/api/user/{id}")
    print(r.text)
    if r.status_code == 400: return abort(404)
    user = U(id=u.id, bio=u.bio, name=r.json()["data"]["username"], avatar_url=r.json()["data"]["avatar"])
    
    bots = Bot.query.filter_by(owner=u.id).all()
    return render_template("user.html", current_user=current_user, discord=get_discord(), wanted_user=user, bots=bots)
    
@app.route("/addbot")
@login_required
def addbot():
    return render_template("addbot.html",current_user=current_user, discord=get_discord())
    

@app.route("/me")
@app.route("/profile")
@login_required
def me():
    
    return render_template("me.html",current_user=current_user, discord=get_discord())

def get_discord():

    class U:
        def __init__(self, **vars):
            for k, v in vars.items():
                setattr(self, k, v)
    print(session["USER"])
    if session["USER"]:
        return U(**session["USER"])
    else:
        return U(name="[ANONYMOUS]",avatar_url="", id=0, accent_color=None,discriminator="0000")


@app.route("/")
def root():
    return render_template("index.html", current_user=current_user, discord=get_discord())



if __name__ == "__main__":
    app.run(debug=True) # assuming you're hosting via actress or nginx
