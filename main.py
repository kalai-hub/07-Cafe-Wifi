from flask import Flask, jsonify, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField
from wtforms.validators import DataRequired, URL
import random

app = Flask(__name__)

app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

Bootstrap5(app)


# CREATE DB
class Base(DeclarativeBase):
    pass


# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
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
def add_new_cafe():
    form = MyForm()
    if form.validate_on_submit():
        new_post = Cafe(
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
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('all_cafe'))
    return render_template('make-cafe.html', form=form)


@app.route("/edit-cafe/<int:cafe_id>", methods=['GET', 'POST'])
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


# HTTP POST - Create Record

@app.route("/add", methods=['POST'])
def add_cafe():
    name = request.form['name']
    map_url = request.form['map_url']
    add_user_cafe = Cafe(
        name=request.form.get("name"),
        map_url=request.form.get("map_url"),
        img_url=request.form.get("img_url"),
        location=request.form.get("loc"),
        has_sockets=bool(request.form.get("sockets")),
        has_toilet=bool(request.form.get("toilet")),
        has_wifi=bool(request.form.get("wifi")),
        can_take_calls=bool(request.form.get("calls")),
        seats=request.form.get("seats"),
        coffee_price=request.form.get("coffee_price")
    )
    print(name)
    print(map_url)
    db.session.add(add_user_cafe)
    db.session.commit()
    return jsonify(response={"success": "Successfully added new cafe"})

# Delete Cafe
@app.route("/delete/<int:cafe_id>")
def delete_cafe(cafe_id):
    cafe = db.session.get(Cafe, cafe_id)
    db.session.delete(cafe)
    db.session.commit()
    return redirect(url_for('all_cafe'))


if __name__ == '__main__':
    app.run(debug=True)
