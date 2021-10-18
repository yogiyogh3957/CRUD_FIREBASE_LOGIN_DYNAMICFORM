from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, FileField, PasswordField
from wtforms.validators import DataRequired, URL, Email, Length

class DataForm(FlaskForm):

    name = StringField("name")
    address = StringField("address")
    image = FileField('image')

    submit = SubmitField('Submit')

class RegisterForm(FlaskForm):
    valid_mail = Email(message="not valid email")
    valid_number = Length(min=4, message="min 4 characters")

    name = StringField("name", validators=[DataRequired()])
    email = StringField("email", validators=[DataRequired(), valid_mail])
    password = PasswordField("password", validators=[DataRequired()])
    submit = SubmitField("Submit")


class LoginForm(FlaskForm):
    valid_mail = Email(message="not valid email")
    valid_number = Length(min=4, message="min 4 characters")

    email = StringField("email", validators=[DataRequired(), valid_mail])
    password = PasswordField("password", validators=[DataRequired()])
    submit = SubmitField("LOGIN")


