from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, FloatField, IntegerField
from wtforms.validators import DataRequired, Email, Length, NumberRange

class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    name = StringField("Name", validators=[DataRequired()])
    gender = SelectField("Gender", choices=[("male", "Male"), ("female", "Female")], validators=[DataRequired()])
    height = FloatField("Height (cm)", validators=[DataRequired(), NumberRange(min=50)])
    weight = FloatField("Weight (kg)", validators=[DataRequired(), NumberRange(min=20)])
    age = IntegerField("Age", validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField("Register")
    

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")
    
class WorkoutForm(FlaskForm):
    exercise = StringField("Enter what you did", validators=[DataRequired()])
    submit = SubmitField("Add")