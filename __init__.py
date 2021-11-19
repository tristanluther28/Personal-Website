import enum
from operator import ge
from re import U
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from flask import Flask, redirect, url_for, render_template, request, session, g, Markup
import datetime
from datetime import date, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import random
from secret import settings

# Create the flask app
app = Flask(__name__)

# Session data needs key for encryption
app.secret_key = settings['APP_SECRET']
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.permanent_session_lifetime = timedelta(days=3) # Session will last for 3 days

# Create referance to Database
db = SQLAlchemy(app)

# Create Database Model for Users who can login
class users(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True) # Primary Key Identifier
    name = db.Column("name", db.String(100))
    email = db.Column("email", db.String(100))
    password_hash = db.Column("password_hash", db.String(128))
    def __init__(self, name, email):
        self.name = name
        self.email = email

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Create Database Model for Books
class books(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True) # Primary Key Identifier
    author = db.Column("author", db.String(100))
    title = db.Column("title", db.String(100))
    genere = db.Column("genere", db.String(100))
    release = db.Column("release", db.DateTime())
    img_url = db.Column("img_url", db.String(100))

    def __init__(self, author, title, genere, release, img_url):
        self.author = author
        self.title = title
        self.genere = genere
        self.release = release
        self.img_url = img_url

# Create Database Model for Skills
class skill(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True) # Primary Key Identifier
    skill_name = db.Column("skill_name", db.String(100))
    confidence_lvl = db.Column("confidence_lvl", db.Integer)
    skill_type = db.Column("skill_type", db.String(100))

    def __init__(self, skill_name, confidence_lvl, skill_type):
        self.skill_name = skill_name
        self.skill_type = skill_type
        self.confidence_lvl = confidence_lvl

# Create Database Model for Work Locations
class work(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True) # Primary Key Identifier
    location = db.Column("location", db.String(100))
    title = db.Column("title", db.String(100))
    long = db.Column("long", db.String(100))
    lat = db.Column("lat", db.String(100))
    start = db.Column("start", db.DateTime())
    end = db.Column("end", db.DateTime())

    def __init__(self, location, title, long, lat, start):
        self.location = location
        self.title = title
        self.long = long
        self.lat = lat
        self.start = start

    def set_end_date(self, end):
        self.end = end

# Create Database Model for category
class proj_category(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True) # Primary Key Identifier
    name = db.Column("name", db.String(100))

    def __init__(self, name):
        self.name = name

# Create Database Model for a project
class project(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True) # Primary Key Identifier
    name = db.Column("name", db.String(100))
    category_id = db.Column("category_id", db.Integer)
    content_md = db.Column("content_md", db.Text)
    github_link = db.Column("github_link", db.String(128))
    model_link = db.Column("model_link", db.String(128))
    cover_img = db.Column("cover_img", db.String(128))
    date_made = db.Column("date_made", db.DateTime())
    date_edit = db.Column("date_edit", db.DateTime())

    def __init__(self, name, category_id, content_md, date_made, cover_img):
        self.name = name
        self.category_id = category_id
        self.content_md = content_md
        self.date_made = date_made
        self.date_edit = date_made
        self.cover_img = cover_img

    def add_github(self, github):
        self.github_link = github

    def add_model(self, model):
        self.model_link = model

# Create Database Model for a item of a bill of materials
class bom_item(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True) # Primary Key Identifier
    name = db.Column("name", db.String(100))
    project_id = db.Column("project_id", db.Integer)
    unit_price = db.Column("unit_price", db.Integer)
    quantity = db.Column("quantity", db.Integer)

    def __init__(self, name, project_id, unit_price, quantity):
        self.name = name
        self.project_id = project_id
        self.unit_price = unit_price
        self.quantity = quantity

# Get the categories for every page
@app.before_request
def before_request():
    category = proj_category.query.all()
    g.category = category

# Define the root directory to be the function home
@app.route("/")
def home():
    return render_template("index.html", projects=project.query.order_by(project.date_made.desc()), categories=proj_category.query.all())

@app.route("/<int:param>")
def category(param):
    # Get all projects under the passed parameter (category_id)
    return render_template("category.html", id=param, category=proj_category.query.get(param), projects=project.query.filter_by(category_id=param).order_by(project.date_made.desc()))

@app.route("/<int:category_id>/<int:project_id_src>")
def project_page(category_id = None, project_id_src = None):
    project_select = project.query.get(project_id_src)
    if project_select.category_id == category_id:
        total_cost = 0
        bom = bom_item.query.filter_by(project_id=project_id_src).all()
        for item in bom:
            total_cost = total_cost + (item.quantity*item.unit_price)
        return render_template("project.html", id=project_id_src, project=project_select, content_md=Markup(project_select.content_md), bom=bom, total=total_cost) # Valid Request send to page with data
    else:
        return redirect("/")

@app.route("/about")
def about():
    # Get Spotify API data
    # Authorize this application
    # Spotify Credientials
    auth_manager = SpotifyClientCredentials(client_id=settings['SPOTIFY_CLIENT_ID'], client_secret=settings['SPOTIFY_CLIENT_SECRET'])
    sp = spotipy.Spotify(auth_manager=auth_manager)
    playlist_id = ""
    playlists = sp.user_playlists('tluther06')
    # Find the playlist with the name My Favorite Song/collect its playlist_id
    while playlists:
        for i, playlist in enumerate(playlists['items']):
            if playlist['name'] == "My Favorite Song":
                playlist_id = playlist["id"]
        if playlists['next']:
            playlists = sp.next(playlists)
        else:
            playlists = None
    # Use the playlist_id and create a list of the songs/details
    songs = sp.playlist(playlist_id=playlist_id)
    random.shuffle(songs['tracks']['items'])
    song_list = []
    for i, song in enumerate(songs['tracks']['items']):
        if i == 6:
            break
        song_list.append(song)
    return render_template("about.html", books=books.query.all(), works=work.query.all(), skills=skill.query.all(), songs=song_list)

# Main edit page with option to edit all articles/add articles/edit books/add books/add category/edit category
@app.route("/content", methods=["POST", "GET"])
def content():
    if "user" in session:
        return render_template("content.html", books=books.query.all(), works=work.query.all(), skills=skill.query.all(), categories=proj_category.query.all(), projects=project.query.order_by(project.date_made.desc())) # Only allow user to reder this template if they are a user
    else:
        return redirect("/")

# Login for users
@app.route("/login",methods=["POST", "GET"])
def login():
    message = ""
    #User is attempting login/check credentials
    if request.method == "POST":
        email = request.form['email']
        raw_pass = request.form['password']
        message = ""
        found_user = users.query.filter_by(email=email).first()
        if found_user:
            # Verify the user password
            if found_user.check_password(raw_pass):
                session["user"] = email # User is logged in, add their data to the session
                session.permanent = True
                return redirect("/content") # Send them to the content page
            else:
                message = "Your password was incorrect"
        else:
            message = "This account does not exist"
    return render_template("login.html",msg=message)

# User has logged out, clear session and redirect
@app.route("/logout")
def logout():
        session.pop("user", None)
        return redirect(url_for("login"))

# Smith Chart Helper Page
@app.route("/smith",methods=["GET", "POST"])
def smith():
    if request.method == "POST":
        freq = request.form["freq"]
        return render_template("chart.html")
    else:
        return render_template("chart.html")

# Add a new book for the user
@app.route("/content/add/book", methods=["POST", "GET"])
def add_book():
    if "user" in session:
        if request.method == "POST":
            title = request.form["title"]
            author = request.form["author"]
            date = datetime.datetime.strptime(request.form["release"], '%Y-%m-%d')
            genere = request.form["genere"]
            img = request.form["img"] # Push this info the database
            book = books(author=author, title=title, genere=genere, release=date, img_url=img)
            db.session.add(book)
            db.session.commit()
            return render_template("add_book.html", msg="Book Successfully Added") # Only allow user to reder this template if they are a user
        else:
            return render_template("add_book.html") # Only allow user to reder this template if they are a user
    else:
        return render_template("index.html") # Only allowed if you are signed-in

# Add a new work location for the user
@app.route("/content/add/work", methods=["POST", "GET"])
def add_work():
    if "user" in session:
        if request.method == "POST":
            title = request.form["title"]
            location = request.form["location"]
            date_start = datetime.datetime.strptime(request.form["start"], '%Y-%m-%d')
            long = request.form["long"]
            lat = request.form["lat"]
            work_place = work(location=location, title=title, start=date_start, lat=lat, long=long)
            if request.form["end"]:
                work_place.set_end_date(datetime.datetime.strptime(request.form["end"], '%Y-%m-%d'))
            db.session.add(work_place)
            db.session.commit()
            return render_template("add_work.html", msg="Job Successfully Added") # Only allow user to reder this template if they are a user
        else:
            return render_template("add_work.html") # Only allow user to reder this template if they are a user
    else:
        return render_template("index.html") # Only allowed if you are signed-in

# Add a new skill for the user
@app.route("/content/add/skill", methods=["POST", "GET"])
def add_skill():
    if "user" in session:
        if request.method == "POST":
            skill_name = request.form["name"]
            skill_type = request.form["type"]
            confidence = request.form["confidence"]
            new_skill = skill(skill_type=skill_type, skill_name=skill_name, confidence_lvl=confidence)
            db.session.add(new_skill)
            db.session.commit()
            return render_template("add_skill.html", msg="Skill Successfully Added") # Only allow user to reder this template if they are a user
        else:
            return render_template("add_skill.html") # Only allow user to reder this template if they are a user
    else:
        return render_template("index.html") # Only allowed if you are signed-in

# Add a new skill for the user
@app.route("/content/add/category", methods=["POST", "GET"])
def add_category():
    if "user" in session:
        if request.method == "POST":
            name = request.form["name"]
            new_category = proj_category(name=name)
            db.session.add(new_category)
            db.session.commit()
            return render_template("add_category.html", msg="Category Successfully Added") # Only allow user to reder this template if they are a user
        else:
            return render_template("add_category.html") # Only allow user to reder this template if they are a user
    else:
        return render_template("index.html") # Only allowed if you are signed-in

# Add a new skill for the user
@app.route("/content/add/bom-item", methods=["POST", "GET"])
def add_bom_item():
    if "user" in session:
        if request.method == "POST":
            name = request.form["name"]
            project_id = request.form["project_id"]
            unit_price = request.form["unit_price"]
            quantity = request.form["quantity"]
            new_bom_item = bom_item(name=name, project_id=project_id, unit_price=unit_price, quantity=quantity)
            db.session.add(new_bom_item)
            db.session.commit()
            return render_template("add_bom_item.html", msg="BOM Item Successfully Added", projects=project.query.all()) # Only allow user to reder this template if they are a user
        else:
            return render_template("add_bom_item.html", projects=project.query.all()) # Only allow user to reder this template if they are a user
    else:
        return render_template("index.html") # Only allowed if you are signed-in

# Add a new project for the user
@app.route("/content/add/project", methods=["POST", "GET"])
def add_project():
    if "user" in session:
        if request.method == "POST":
            name = request.form["name"]
            content_md = request.form["content_md"]
            category_id = request.form["category_id"]
            cover_img = request.form["cover_img"]
            new_project = project(name=name, content_md=content_md, category_id=category_id, date_made=datetime.datetime.now(), cover_img=cover_img)
            if request.form["github_link"]:
                new_project.add_github(request.form["github_link"])
            if request.form["model_link"]:
                new_project.add_model(request.form["model_link"])
            db.session.add(new_project)
            db.session.commit()
            return render_template("add_project.html", msg="Project Successfully Added", categories=proj_category.query.all()) # Only allow user to reder this template if they are a user
        else:
            return render_template("add_project.html", categories=proj_category.query.all()) # Only allow user to reder this template if they are a user
    else:
        return render_template("index.html") # Only allowed if you are signed-in

# Edit a project for the user
@app.route("/content/edit/project/<int:param>", methods=["POST", "GET"])
def edit_project(param):
    if "user" in session:
        if request.method == "POST":
            edit_project = project.query.filter_by(_id=param).first()
            edit_project.name = request.form["name"]
            edit_project.content_md = request.form["content_md"]
            edit_project.category_id = request.form["category_id"]
            edit_project.cover_img = request.form["cover_img"]
            edit_project.date_edit = datetime.datetime.now()
            if request.form["github_link"]:
                edit_project.github_link = request.form["github_link"]
            if request.form["model_link"]:
                edit_project.model_link = request.form["model_link"]
            if request.form["date_made"]:
                edit_project.date_made = datetime.datetime.strptime(request.form["date_made"], '%Y-%m-%d')
            db.session.commit()
            return render_template("edit_project.html", msg="Project Successfully Updated", categories=proj_category.query.all(), project=edit_project, date_made=edit_project.date_made.strftime("%Y-%m-%d")) # Only allow user to reder this template if they are a user
        else:
            select_project = project.query.filter_by(_id=param).first()
            return render_template("edit_project.html", categories=proj_category.query.all(), project=select_project, date_made=select_project.date_made.strftime("%Y-%m-%d")) # Only allow user to reder this template if they are a user
    else:
        return render_template("index.html") # Only allowed if you are signed-in

# Custom 404 Page
@app.errorhandler(404)
def not_found(e):
    return redirect("/")

# Starts the server running at port 5001!
if __name__ == "__main__":
    db.create_all() # Create the SQLAlchemy database
    app.run(port=5001,debug=False,ssl_context=(settings['FULLCHAIN'], settings['SECRET_KEY']))