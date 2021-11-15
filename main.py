from flask import Flask, render_template, redirect, request, url_for, Response, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
import os
import pyrebase
from forms import DataForm, RegisterForm, LoginForm
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_wtf.csrf import CSRFProtect

import datetime
timezone_diff = datetime.timedelta(hours = 7)
GMT_timezone = datetime.timezone(timezone_diff)
x = datetime.datetime.now(GMT_timezone)

day = x.strftime('%x')
clock = x.strftime('%X')
full = x.strftime('%c')

SAVED_LOC = os.path.join('static', 'uploads')
CV_LOC = os.path.join('static', 'myfile')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'SECRET KEY'
Bootstrap(app)
csrf = CSRFProtect(app)

admin_id = [1, 2]
##login conf
login_manager = LoginManager()
login_manager.init_app(app)

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try :
            #login tapi bukan admin, cek list admin di admin_id
            if current_user.id not in admin_id:
                # return redirect(url_for('login'))
                return abort(403)
        #tidak login, jadi gapunya id
        except AttributeError :
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return User_db.query.get(int(user_id))


#firebase conf
conf = {
  "apiKey": "AIzaSyCBQHxjNEnEloJfyGmUefzbvg7omK50X-4",
  "authDomain": "connectpython-b6161.firebaseapp.com",
  "projectId": "connectpython-b6161",
  "storageBucket": "connectpython-b6161.appspot.com",
  "serviceAccount" : "serviceAccountKey.json",
  "databaseURL": ""
}
firebase_storage = pyrebase.initialize_app(conf)
storage = firebase_storage.storage()

#db_conf
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///image_firebase_login.db'
db = SQLAlchemy(app)

class Data_db(db.Model):
    __tablename__ = "people_data"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True)
    address = db.Column(db.Text, unique=True)
    image = db.Column(db.Text, nullable=False)
    date = db.Column(db.Text, nullable=False)

    inputer_name = db.Column(db.Text, db.ForeignKey("users.id"))
    inputer = relationship("User_db", back_populates="people_data")

class User_db(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    #parents
    people_data = relationship("Data_db", back_populates="inputer")

db.create_all()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/login", methods=['POST', 'GET'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        #retrieve data from form loginform
        email = form.email.data
        password = form.password.data

        user = User_db.query.filter_by(email=email).first()

        if not user:
            print("email salah/paswword salah")
            flash("Email not Registered, please REGISTER!")
            return redirect(url_for("register"))
        if not check_password_hash(user.password, password):
            flash("WRONG PASSWORD")
            print("wrong password")
            return redirect(url_for("login"))

        else:
            print("login success")
            login_user(user)
            return render_template("indexv3.html", logged_in = True)
    return render_template("loginv3.html", form=form)


@app.route("/register", methods=['POST', 'GET'])
def register():

    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data
        hashed_password = generate_password_hash(password=password, method='pbkdf2:sha256', salt_length=8)

        user_entry = User_db(
            name=name,
            email=email,
            password=hashed_password
        )
        #cek same email in DB(email has been registered ?)
        if User_db.query.filter_by(email=email).first():
            flash("Email Already Registered, please login!")
            return redirect(url_for('login'))
        else:
            db.session.add(user_entry)
            db.session.commit()
            flash("Register Success, please login!")
            return redirect(url_for('login'))

    return render_template("registerv3.html", form=form)


@app.route("/", methods=['POST', 'GET'])
def home():

    if request.method == 'POST':
        file = request.files['file']
        print(file.filename)

        if file and allowed_file(file.filename) :
            file_name = file.filename
            images = file.save(os.path.join(SAVED_LOC, file_name))

            #firebase saved image location, masuk folder image
            firebase_path = f"images/{file_name}"

            #upload
            local_path_up = f"{SAVED_LOC}/{file_name}"
            storage.child(firebase_path).put(local_path_up)

            #setelah  terupload @firebase, di remove @local
            os.remove(local_path_up)

            # #download
            # local_path_down = f"{SAVED_LOC}/download/{file_name}"
            # storage.child(firebase_path).download(local_path_down)

            #get image url from firebase
            image_url = storage.child(firebase_path).get_url(file_name)

            return render_template('showdatav3.html', image_url=image_url, filename=f"uploads/{file_name}", has_image = True, logged_in=False, current_user=current_user)

    return render_template("indexv3.html", current_user=current_user)

@app.route('/add', methods=["GET", "POST"])
def add():
    print(current_user.id)
    form = DataForm()

    if form.validate_on_submit():

        image = request.files.get("image")

        print(image.filename)

        if image and allowed_file(image.filename):

            file_name = image.filename
            image.save(os.path.join(SAVED_LOC, file_name))

            firebase_path = f"images/{file_name}"
            local_path_up = f"{SAVED_LOC}/{file_name}"
            storage.child(firebase_path).put(local_path_up)
            os.remove(local_path_up)

            image_url = storage.child(firebase_path).get_url(file_name)

            user_entry = Data_db(
                name=request.form.get("name"),
                address=request.form.get("address"),
                image=image_url,
                inputer=current_user,
                date = full
                )
            db.session.add(user_entry)
            db.session.commit()

            return redirect(url_for("showdata"))
    return render_template("addv3.html", form=form, current_user=current_user)

@app.route("/edit-post/<int:data_id>", methods=["GET", "POST"])
@admin_only
def edit_post(data_id):
    data_to_edit = Data_db.query.get(data_id)
    image_url = data_to_edit.image
    print(image_url)

    edit_form = DataForm(
        name=data_to_edit.name,
        address=data_to_edit.address,
        image=data_to_edit.image,
    )

    if edit_form.validate_on_submit():

        image = request.files.get("image")

        if image and allowed_file(image.filename):

            file_name = image.filename
            image.save(os.path.join(SAVED_LOC, file_name))

            firebase_path = f"images/{file_name}"
            local_path_up = f"{SAVED_LOC}/{file_name}"
            storage.child(firebase_path).put(local_path_up)
            os.remove(local_path_up)

            image_url = storage.child(firebase_path).get_url(file_name)

            data_to_edit.name = edit_form.name.data
            data_to_edit.address = edit_form.address.data
            data_to_edit.image = image_url

            db.session.commit()
            return redirect(url_for('showdata'))

        #if not change photos
        else:

            data_to_edit.name = edit_form.name.data
            data_to_edit.address = edit_form.address.data
            data_to_edit.image = data_to_edit.image

            db.session.commit()
            return redirect(url_for('showdata'))

    return render_template("edit.html", form=edit_form, edit=True, data=data_to_edit)

@app.route('/showdata', methods=["GET", "POST"])
def showdata():
    user_name_list = []
    data = Data_db.query.all()
    for x in data :
        user_name_list.append(User_db.query.get(x.inputer_name).name)

    return render_template("showdatav3.html", data=data, user_name_list=user_name_list)

@app.route('/delete/<int:data_id>')
@admin_only
def delete_post(data_id):
    data_to_delete = Data_db.query.get(data_id)
    db.session.delete(data_to_delete)
    db.session.commit()
    return redirect(url_for('showdata'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/aboutme')
def aboutme():

    return render_template("aboutme.html", filename="/static/myfile/mycv.pdf")


if __name__=="__main__":
    app.run(host=os.getenv('IP', '0.0.0.0'),
            port=int(os.getenv('PORT', 8943)), debug=True)


