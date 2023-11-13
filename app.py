import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import re
from time import mktime, strptime

from helpers import login_required

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

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finalproject.db")

@app.route("/")
@login_required
def index():
    snips = db.execute("SELECT name,username,sniptext,snips.id,timestamp FROM snips JOIN users ON snips.user_id = users.id WHERE ((user_id IN (SELECT following_id from follow WHERE follower_id = ?)) OR (user_id = ?)) ORDER BY timestamp DESC", session["user_id"], session["user_id"])
    resnips = db.execute("SELECT rsusers.name AS rsname, snipusers.name, snipusers.username, sniptext, snips.id, resnips.timestamp FROM resnips JOIN snips on snips.id = resnips.snip_id JOIN users snipusers ON snips.user_id = snipusers.id JOIN users rsusers ON resnips.resnipper_id = rsusers.id WHERE ((rsusers.id IN (SELECT following_id from follow WHERE follower_id = ?)) OR (rsusers.id = ?))", session["user_id"], session["user_id"])
    #get replysnips to work with resnips
    snipdata = snips+resnips

    snipdata.sort(key = lambda x: mktime(strptime(x["timestamp"], "%Y-%m-%d %H:%M:%S")), reverse=True)

    return render_template("index.html", snipdata=snipdata)

@app.route("/follow", methods=["POST"])
@login_required
def follow():
    following = request.form.get("following")
    if db.execute("SELECT * FROM users WHERE username=?", following) and not db.execute("SELECT * FROM follow WHERE follower_id=? AND following_id = (SELECT id FROM users WHERE username=?)", session["user_id"], following) and not (db.execute("SELECT id FROM users WHERE username = ?", following)[0]["id"] == session["user_id"]):
        db.execute("INSERT INTO follow(follower_id, following_id) VALUES(?, (SELECT id FROM users WHERE username = ?))", session["user_id"], following)
        return "", 201
    return "", 403

@app.route("/like", methods=["POST"])
@login_required
def like():
    sniptype = request.form.get("sniptype")
    snipid = request.form.get("snipid")
    if sniptype == "snippet":
        if db.execute("SELECT * FROM snips WHERE id=?", snipid) and not db.execute("SELECT * FROM likes WHERE snip_id=? AND liker_id = ?", snipid, session["user_id"]):
            db.execute("INSERT INTO likes(snip_id, liker_id) VALUES(?, ?)", snipid, session["user_id"])
            likecount = db.execute("SELECT COUNT(liker_id) FROM likes WHERE snip_id = ?", snipid)[0]["COUNT(liker_id)"]
            return "Like", likecount, 201
        if db.execute("SELECT * FROM snips WHERE id=?", snipid) and db.execute("SELECT * FROM likes WHERE snip_id=? AND liker_id = ?", snipid, session["user_id"]):
            db.execute("DELETE FROM likes WHERE snip_id=? AND liker_id=?", snipid, session["user_id"])
            likecount = db.execute("SELECT COUNT(liker_id) FROM likes WHERE snip_id = ?", snipid)[0]["COUNT(liker_id)"]
            return "Unlike", likecount, 201
    elif sniptype == "replysnippet":
        if db.execute("SELECT * FROM replies WHERE id=?", snipid) and not db.execute("SELECT * FROM likes WHERE reply_id=? AND liker_id = ?", snipid, session["user_id"]):
            db.execute("INSERT INTO likes(reply_id, liker_id) VALUES(?, ?)", snipid, session["user_id"])
            return "Like", 201
        if db.execute("SELECT * FROM replies WHERE id=?", snipid) and db.execute("SELECT * FROM likes WHERE reply_id=? AND liker_id = ?", snipid, session["user_id"]):
            db.execute("DELETE FROM likes WHERE reply_id=? AND liker_id=?", snipid, session["user_id"])
            return "Unlike", 201
    return "", 403

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("login.html", message="must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html", message="must provide password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["passhash"], request.form.get("password")):
            return render_template("login.html", message="invalid username and/or password")

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

@app.route("/profile/<username>")
@login_required
def profile(username):
    if db.execute("SELECT * FROM users WHERE username = ?", username):
        if db.execute("SELECT * FROM follow WHERE following_id = (SELECT id FROM users WHERE username = ?) AND follower_id = ?", username, session["user_id"]):
            isfollowing = True
        else:
            isfollowing = False
        userinfo = db.execute("SELECT name,username,bio FROM users WHERE username = ?", username)[0]
        snips = db.execute("SELECT name,username,sniptext,snips.id FROM snips JOIN users ON snips.user_id = users.id WHERE username = ? ORDER BY timestamp DESC", username)
        follower_count = int(db.execute("SELECT COUNT(follower_id) FROM follow WHERE following_id = (SELECT id FROM users WHERE username = ?)", username)[0]["COUNT(follower_id)"])
        following_count = int(db.execute("SELECT COUNT(following_id) FROM follow WHERE follower_id = (SELECT id FROM users WHERE username = ?)", username)[0]["COUNT(following_id)"])
        return render_template("profile.html", isfollowing=isfollowing, userinfo=userinfo, snips=snips, follower_count=follower_count, following_count=following_count)
    else:
        return "User not found", 404

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        if not request.form.get("name"):
            return render_template("register.html", message="must provide name")
        elif not request.form.get("day") or not request.form.get("month") or not request.form.get("year"):
            return render_template("register.html", message="must provide birthday")
        elif not request.form.get("username"):
            return render_template("register.html", message="must provide username")
        elif not request.form.get("password"):
            return render_template("register.html", message="must provide password")
        elif db.execute("SELECT * FROM users WHERE username=?", request.form.get("username")):
            return render_template("register.html", message="username already taken")
        elif request.form.get("password") != request.form.get("confirmation"):
            return render_template("register.html", message="passwords do not match")
        elif len(request.form.get("password")) < 8:
            return render_template("register.html", message="password is not at least eight letters")
        elif not re.search("[0-9]", request.form.get("password")):
            return render_template("register.html", message="password does not have any numbers")
        elif not re.search("[A-Z]", request.form.get("password")):
            return render_template("register.html", message="password does not have any capital letters")
        elif not re.search("[^A-Za-z0-9]", request.form.get("password")):
            return render_template("register.html", message="password does not have any special characters")
        else:
            birthday = request.form.get("year")+"-"+request.form.get("month")+"-"+request.form.get("day")
            db.execute("INSERT INTO users (username, passhash, name, birthday) VALUES(?, ?, ?, ?)", request.form.get("username"), generate_password_hash(request.form.get("password")), request.form.get("name"), birthday)
            session["user_id"] = db.execute("SELECT id FROM users WHERE username = ?", request.form.get("username"))[0]["id"]
            return redirect("/")

    else:
        return render_template("register.html")

@app.route("/reply", methods=["POST"])
@login_required
def reply():
    snipid = request.form.get("snipid")
    sniptype = request.form.get("sniptype")
    replytext = request.form.get("replydata")
    if sniptype == "snippet":
        db.execute("INSERT INTO replies(snip_id, replier_id, replytext, timestamp) VALUES(?, ?, ?, DATETIME())", snipid, session["user_id"], replytext)
        username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]["username"]
        name = db.execute("SELECT name FROM users WHERE id = ?", session["user_id"])[0]["name"]
    elif sniptype == "replysnippet":
        db.execute("INSERT INTO replies(reply_id, replier_id, replytext, timestamp) VALUES(?, ?, ?, DATETIME())", snipid, session["user_id"], replytext)
        username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]["username"]
        name = db.execute("SELECT name FROM users WHERE id = ?", session["user_id"])[0]["name"]

    return jsonify({"username":username, "name": name, "replytext": replytext})

@app.route("/replysnippet/<reply_id>")
@login_required
def replysnippet(reply_id):
    if db.execute("SELECT * FROM replies WHERE id = ?", reply_id):
        snip = db.execute("SELECT name,username,replytext,replies.id FROM replies JOIN users ON replies.replier_id = users.id WHERE replies.id = ?", reply_id)[0]
        snip["likes"] = db.execute("SELECT COUNT(liker_id) FROM likes WHERE reply_id = ?", reply_id)[0]["COUNT(liker_id)"]
        snip["resnips"] = db.execute("SELECT COUNT(resnipper_id) FROM resnips WHERE reply_id = ?", reply_id)[0]["COUNT(resnipper_id)"]
        replies = db.execute("SELECT name,username,replytext,replies.id FROM replies JOIN users ON replies.replier_id = users.id WHERE reply_id = ?", reply_id)
        print(f"Replies: {replies}")
        parentreplysnippetids = []
        if db.execute("SELECT reply_id FROM replies WHERE replies.id = ?", reply_id)[0]["reply_id"]:
            parentreplysnippet = db.execute("SELECT reply_id FROM replies WHERE replies.id = ?", reply_id)[0]["reply_id"]
            parentreplysnippetids.insert(0, parentreplysnippet)
            while db.execute("SELECT reply_id FROM replies WHERE replies.id = ?", parentreplysnippet)[0]["reply_id"]:
                parentreplysnippet = db.execute("SELECT reply_id FROM replies WHERE replies.id = ?", parentreplysnippet)[0]["reply_id"]
                parentreplysnippetids.insert(0, parentreplysnippet)
            parentsnippet = db.execute("SELECT snip_id FROM replies WHERE replies.id = ?", parentreplysnippet)[0]["snip_id"]
        else:
            parentsnippet = db.execute("SELECT snip_id FROM replies WHERE replies.id = ?", reply_id)[0]["snip_id"]

        print(f"Parent Snippet: {parentsnippet}")
        print(f"Parent Reply Snippets: {parentreplysnippetids}")

        parentsnippet = db.execute("SELECT name,username,sniptext,snips.id FROM snips JOIN users ON snips.user_id = users.id WHERE snips.id = ?", parentsnippet)[0]
        parentreplysnippets = []
        for parentreplysnippetid in parentreplysnippetids:
            parentreplysnippets.append(db.execute("SELECT name,username,replytext,replies.id FROM replies JOIN users ON replies.replier_id = users.id WHERE replies.id = ?", parentreplysnippetid)[0])
        
        print(parentsnippet)
        print(parentreplysnippets)

        return render_template("replyview.html", snip=snip, replies=replies, parentsnippet=parentsnippet, parentreplysnippets=parentreplysnippets)
    else:
        return "Snip not found", 404

@app.route("/resnip", methods=["POST"])
@login_required
def resnip():
    sniptype = request.form.get("sniptype")
    snipid = request.form.get("snipid")
    if sniptype == "snippet":
        if db.execute("SELECT * FROM snips WHERE id=?", snipid) and not db.execute("SELECT * FROM resnips WHERE snip_id=? AND resnipper_id = ?", snipid, session["user_id"]):
            db.execute("INSERT INTO resnips(snip_id, resnipper_id, timestamp) VALUES(?, ?, DATETIME())", snipid, session["user_id"])
            return "", 201
    elif sniptype == "replysnippet":
        if db.execute("SELECT * FROM replies WHERE id=?", snipid) and not db.execute("SELECT * FROM resnips WHERE reply_id=? AND resnipper_id = ?", snipid, session["user_id"]):
            db.execute("INSERT INTO resnips(reply_id, resnipper_id, timestamp) VALUES(?, ?, DATETIME())", snipid, session["user_id"])

    return "", 403

@app.route("/usersearch")
@login_required
def usersearch():
    q = request.args.get("q")
    if q:
        results = db.execute("SELECT * FROM users WHERE username LIKE ? ORDER BY UPPER(username) LIMIT 5;", "%"+q+"%")
    else:
        results = []
        
    return jsonify(results)

@app.route("/snip", methods=["POST"])
@login_required
def snip():
    sniptext = request.form.get("snipdata")
    db.execute("INSERT INTO snips(user_id, sniptext, timestamp) VALUES(?, ?, DATETIME())", session["user_id"], sniptext)
    username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]["username"]
    name = db.execute("SELECT name FROM users WHERE id = ?", session["user_id"])[0]["name"]

    return jsonify({"username":username, "name": name, "sniptext": sniptext})

@app.route("/snippet/<snip_id>")
@login_required
def snippet(snip_id):
    if db.execute("SELECT * FROM snips WHERE id = ?", snip_id):
        snip = db.execute("SELECT name,username,sniptext,snips.id FROM snips JOIN users ON snips.user_id = users.id WHERE snips.id = ?", snip_id)[0]
        snip["likes"] = db.execute("SELECT COUNT(liker_id) FROM likes WHERE snip_id = ?", snip_id)[0]["COUNT(liker_id)"]
        snip["resnips"] = db.execute("SELECT COUNT(resnipper_id) FROM resnips WHERE snip_id = ?", snip_id)[0]["COUNT(resnipper_id)"]
        replies = db.execute("SELECT name,username,replytext,replies.id FROM replies JOIN users ON replies.replier_id = users.id WHERE snip_id = ?", snip_id)
        print(f"Replies: {replies}")
        return render_template("snippetview.html", snip=snip, replies=replies)
    else:
        return "Snip not found", 404

@app.route("/unfollow", methods=["POST"])
@login_required
def unfollow():
    unfollowing = request.form.get("unfollowing")
    if db.execute("SELECT * FROM users WHERE username=?", unfollowing) and db.execute("SELECT * FROM follow WHERE follower_id = ? AND following_id = (SELECT id FROM users WHERE username = ?)", session["user_id"], unfollowing) and not (db.execute("SELECT id FROM users WHERE username = ?", unfollowing)[0]["id"] == session["user_id"]):
        db.execute("DELETE FROM follow WHERE follower_id = ? AND following_id = (SELECT id FROM users WHERE username = ?)", session["user_id"], unfollowing)
        return "", 201
    return "", 403

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return e.name, e.code


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)