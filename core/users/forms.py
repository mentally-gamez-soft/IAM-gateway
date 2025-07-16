"""Represent the forms for any input users."""

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    EmailField,
    PasswordField,
    StringField,
)
from wtforms.validators import DataRequired, Email, Length


class LoginForm(FlaskForm):
    """Declare the form for a user to log in.

    Args:
        FlaskForm (_type_): The form that will be checked.
    """

    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
        ],
    )
    remember_me = BooleanField("Remember me")


class SignupForm(FlaskForm):
    """Declare the form class for users management."""

    username = StringField(
        "Name",
        validators=[
            DataRequired(),
            Length(max=64),
        ],
    )
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
        ],
    )
    role = StringField(
        "Role",
        validators=[
            DataRequired(),
            Length(max=64),
        ],
    )
