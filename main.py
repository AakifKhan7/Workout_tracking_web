from flask import Flask, abort, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from werkzeug.security import generate_password_hash, check_password_hash
import datetime, requests, os
from dotenv import load_dotenv
from forms import RegisterForm, LoginForm, WorkoutForm
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA3O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)


login_manager = LoginManager()
login_manager.init_app(app)
load_dotenv()

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///workout.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)
    
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    gender: Mapped[str] = mapped_column(String(10))
    height: Mapped[float] = mapped_column(Float)
    weight: Mapped[float] = mapped_column(Float)
    age: Mapped[int] = mapped_column(Integer)
    workouts = relationship("WorkOut", back_populates="user")
    
class WorkOut(db.Model):
    __tablename__ = "WorkOut"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('users.id'))
    date: Mapped[str] = mapped_column(String(100))
    exercise_name: Mapped[str] = mapped_column(String(100))
    duration_min: Mapped[float] = mapped_column(db.Float)
    calories: Mapped[float] = mapped_column(db.Float)
    user = relationship("User", back_populates="workouts")
    
with app.app_context():
    db.create_all()
    
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
            gender=form.gender.data,
            height=form.height.data,
            weight=form.weight.data,
            age=form.age.data
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        
        return redirect(url_for('get_all_workouts'))
    return render_template("register.html", form = form)

@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('get_all_workouts'))
        
    return render_template("login.html", form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_workouts'))

@app.route('/')
def get_all_workouts():
    # result = db.session.execute(db.select(WorkOut))
    if current_user.is_authenticated:
        workouts = db.session.query(WorkOut).filter_by(user_id=current_user.id).all()
    else:
        workouts = []
    return render_template("index.html", all_workouts=workouts)

@login_required
@app.route('/add_workout', methods=["GET", "POST"])
def add_workout():
    form = WorkoutForm()
    
    if form.validate_on_submit():
        gender = current_user.gender
        weight = current_user.weight
        height = current_user.height
        age = current_user.age

        app_id = os.getenv("DAY_96_APP_ID")
        api_key = os.getenv("nutritionix_API_KEY")
        print("APP_ID:", app_id)
        print("API_KEY:", api_key)

        exercise_endpoint = "https://trackapi.nutritionix.com/v2/natural/exercise"


        headers = {
            'Content-Type': 'application/json',
            'x-app-id': app_id ,
            'x-app-key':api_key
        }
        exercise_text = form.exercise.data

        prams = {
            "query": exercise_text,
            "gender" : gender,
            "weight_kg" : weight,
            "height_cm": height,
            "age": age
        }

        response = requests.post(url=exercise_endpoint, json=prams, headers= headers)
        result = response.json()
        print(result)

        for exercise in result["exercises"]:
            new_workout = WorkOut(
                user_id=current_user.id,
                date=datetime.datetime.now().strftime("%d/%m/%Y"),
                exercise_name=exercise["name"],
                duration_min=exercise["duration_min"],
                calories=exercise["nf_calories"]
            )
            db.session.add(new_workout)
        db.session.commit()
        
        flash("Workout added successfully!")
        return redirect(url_for("get_all_workouts"))
    
    return render_template("add_workout.html", form=form)

def create_donut_chart(workouts):
    from collections import defaultdict
    calories_data = defaultdict(float)

    for workout in workouts:
        calories_data[workout.exercise_name] += workout.calories

    exercises = list(calories_data.keys())
    calories = list(calories_data.values())

    plt.figure(figsize=(8, 8))
    plt.pie(calories, labels=exercises, autopct='%1.1f%%', startangle=90, wedgeprops={'width': 0.3})

    center_circle = plt.Circle((0, 0), 0.70, fc='white')
    plt.gca().add_artist(center_circle)

    plt.title("Calories Burned by Exercise")

    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()

    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return image_base64

@app.route('/calories_chart')
@login_required
def calories_chart():
    if current_user.is_authenticated:
        workouts = db.session.query(WorkOut).filter_by(user_id=current_user.id).all()
        chart_image = create_donut_chart(workouts)
        return render_template("calories_chart.html", chart_image=chart_image)
    else:
        return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True, port=5002)