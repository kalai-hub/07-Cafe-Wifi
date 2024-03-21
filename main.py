from flask import Flask, jsonify, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField
from wtforms.validators import DataRequired, URL
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from forms import RegisterForm, LoginForm
from flask import Flask, abort, render_template, redirect, url_for, flash
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from werkzeug.security import generate_password_hash, check_password_hash
import random
from functools import wraps
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')

Bootstrap5(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)


# CREATE DB
class Base(DeclarativeBase):
    pass


# Connect to Database
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///posts.db")
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# Cafe TABLE Configuration
class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(1000))


class MyForm(FlaskForm):
    name = StringField(label="Cafe Name", validators=[DataRequired()])
    location = StringField(label="Location", validators=[DataRequired()])
    seats = StringField(label="No of seats", validators=[DataRequired()])
    coffee_price = StringField(label="Coffee Price", validators=[DataRequired()])
    map_url = StringField(label="Map URL", validators=[DataRequired()])
    img_url = StringField(label="Image URL", validators=[DataRequired(), URL()])
    wifi = BooleanField(label="WiFi")
    toilet = BooleanField(label="Toilet")
    sockets = BooleanField(label="Sockets")
    calls = BooleanField(label="Can take calls")
    submit = SubmitField(label="Submit")


with app.app_context():
    db.create_all()


# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        user_exist = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if user_exist:
            flash("You have already signed up with that email, please login.")
            return redirect(url_for('login'))
        new_user = User(
            email=form.email.data,
            password=generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8),
            name=form.name.data
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))
    return render_template("register.html", form=form)


# TODO: Retrieve a user from the database based on their email.
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if user is None:
            flash("The email doesn't exist, please try again")
            return redirect(url_for('login'))
        elif check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash("Password incorrect, please try again")
            return redirect(url_for('login'))
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


# TODO: Use a decorator so only an admin user can create a new post
def admin_only(fun):
    @wraps(fun)
    def decorated_function(*args, **kwargs):
        if current_user.get_id() != '1':
            return abort(403)
        return fun(*args, **kwargs)

    return decorated_function


def user_only(fun):
    @wraps(fun)
    def decorated_function(*args, **kwargs):
        if not current_user.get_id():
            return abort(403)
        return fun(*args, **kwargs)

    return decorated_function


@app.route("/")
def home():
    result = db.session.execute(db.select(Cafe).order_by(Cafe.name))
    all_cafes = result.scalars().all()
    return render_template("index.html", all_cafes=all_cafes)


def to_dict(cafe):
    json_dict = {column.name: getattr(cafe, column.name) for column in cafe.__table__.columns}
    return json_dict


# HTTP GET - Read Record
@app.route("/random")
def get_random_cafe():
    result = db.session.execute(db.select(Cafe))
    all_cafes = result.scalars().all()
    random_cafe = random.choice(all_cafes)
    return jsonify(cafe=to_dict(random_cafe))


@app.route("/all")
def all_cafe():
    result = db.session.execute(db.select(Cafe).order_by(Cafe.name))
    all_cafes = result.scalars().all()
    return render_template("index.html", all_cafes=all_cafes)


# show cafe
@app.route('/cafe/<int:cafe_id>')
def show_cafe(cafe_id):
    requested_cafe = db.session.get(Cafe, cafe_id)
    return render_template("cafe.html", cafe=requested_cafe)


# Add cafe
@app.route("/new-cafe", methods=['GET', 'POST'])
@user_only
def add_new_cafe():
    form = MyForm()
    if form.validate_on_submit():
        new_cafe = Cafe(
            name=form.name.data,
            location=form.location.data,
            seats=form.seats.data,
            coffee_price=form.coffee_price.data,
            map_url=form.map_url.data,
            img_url=form.img_url.data,
            has_wifi=form.wifi.data,
            has_toilet=form.toilet.data,
            has_sockets=form.sockets.data,
            can_take_calls=form.calls.data
        )
        db.session.add(new_cafe)
        db.session.commit()
        return redirect(url_for('all_cafe'))
    return render_template('make-cafe.html', form=form)


@app.route("/edit-cafe/<int:cafe_id>", methods=['GET', 'POST'])
@admin_only
def edit_cafe(cafe_id):
    edit = True
    cafe = db.session.get(Cafe, cafe_id)
    edit_form = MyForm(
        name=cafe.name,
        location=cafe.location,
        seats=cafe.seats,
        coffee_price=cafe.coffee_price,
        map_url=cafe.map_url,
        img_url=cafe.img_url,
        wifi=cafe.has_wifi,
        toilet=cafe.has_toilet,
        sockets=cafe.has_sockets,
        calls=cafe.can_take_calls
    )
    if edit_form.validate_on_submit():
        cafe.name = edit_form.name.data
        cafe.location = edit_form.location.data
        cafe.seats = edit_form.seats.data
        cafe.coffee_price = edit_form.coffee_price.data
        cafe.map_url = edit_form.map_url.data
        cafe.img_url = edit_form.img_url.data
        cafe.has_wifi = edit_form.wifi.data
        cafe.has_toilet = edit_form.toilet.data
        cafe.has_sockets = edit_form.sockets.data
        cafe.can_take_calls = edit_form.calls.data
        db.session.commit()
        return redirect(url_for('show_cafe', cafe_id=cafe_id))
    return render_template('make-cafe.html', edit=edit, form=edit_form)


@app.route("/search")
def location():
    loc = request.args.get('loc').title()
    result = db.session.execute(db.select(Cafe).where(Cafe.location == loc))
    all_cafes = result.scalars().all()
    if not all_cafes:
        return jsonify(error={"Not Found": "Sorry, we don't have a cafe at that location"})
    return jsonify(cafes=[to_dict(cafe) for cafe in all_cafes])


# Delete Cafe
@app.route("/delete/<int:cafe_id>")
@admin_only
def delete_cafe(cafe_id):
    cafe = db.session.get(Cafe, cafe_id)
    db.session.delete(cafe)
    db.session.commit()
    return redirect(url_for('all_cafe'))

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == '__main__':
    app.run(debug=False)
