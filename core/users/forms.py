"""Represent the forms for any input users."""

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    EmailField,
    PasswordField,
    StringField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, Length, Optional


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


class ProfileUpdateForm(FlaskForm):
    """Form for updating the authenticated user's profile (US-011).

    All fields are optional — only supplied fields are updated.
    Protected fields (email, username, password, roles) are intentionally
    excluded from this form.
    """

    display_name = StringField(
        "Display Name",
        validators=[Optional(), Length(max=80)],
    )
    avatar_url = StringField(
        "Avatar URL",
        validators=[Optional(), Length(max=255)],
    )
    bio = TextAreaField(
        "Bio",
        validators=[Optional()],
    )
    language_preference = StringField(
        "Language Preference",
        validators=[Optional(), Length(min=2, max=5)],
    )
    timezone = StringField(
        "Timezone",
        validators=[Optional(), Length(max=50)],
    )
