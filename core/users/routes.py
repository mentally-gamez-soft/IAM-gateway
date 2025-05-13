"""Define the routes for the users module."""

import uuid
from urllib.parse import urlparse

from flask import (
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf import FlaskForm

from config.default import (
    JWT_ENCODING_PARAM_1,
    JWT_ENCODING_PARAM_2,
    JWT_ENCODING_PARAM_3,
    SECRET_KEY,
    SECURITY_PASSWORD_SALT,
)
from core import login_manager
from core.auth.generic_encoder_decoder import (
    encode_as_base64,
)
from core.auth.jwt.jwt_handler import decode_jwt, generate_jwt
from core.auth.middlewares.validation_token import (
    confirm_activation_token,
    generate_activation_token,
)
from core.common.credentials_validator import validate_account
from core.common.error_codes import (
    __RESPONSE_STATUS_200,
    __RESPONSE_STATUS_403,
    __RESPONSE_STATUS_422,
)
from core.common.messages import (
    __ACCOUNT_ACTIVATED,
    __ACTIVATION_SUCCESSFUL,
    __DEMAND_RENEW_ACTIVATION,
    __EMAIL_RESENT,
    __GENERIC_ERROR,
    __INVALID_TOKEN_ERROR,
    __SIGNUP_SUCCESSFUL,
    __USER_CREATION_ERROR,
    __USER_WITH_EMAIL_ALREADY_EXISTS,
    __WELCOME_BACK,
)
from core.users import users_bp
from core.users.forms import SignupForm
from core.users.models import GwUser


def initiate_session_jwt(payload, lifetime_in_minutes: int = 30) -> str:
    """Create the jwt from a payload.

    Args:
        payload (dict): the data bond to the jwt.
        lifetime_in_minutes (int, optional): The expiration time in minutes for the token. Defaults to 30 mins.

    Returns:
        str: the jwt token.
    """
    return generate_jwt(payload=payload, lifetime=lifetime_in_minutes)


@login_manager.user_loader
def load_user(user_id: uuid):
    """Load the user session.

    Args:
        user_id (uuid): The id of the user.

    Returns:
        user: an instance for the logged in user.
    """
    return GwUser.get_by_id(user_id)


@users_bp.route(
    "/signup/",
    methods=("POST",),
)
def signup():
    """Define the signup endpoint."""
    if current_user.is_authenticated:
        return (
            jsonify(
                {"message": __WELCOME_BACK, "status": __RESPONSE_STATUS_200}
            ),
            __RESPONSE_STATUS_200,
        )

    form = SignupForm(data=request.get_json())
    error = None

    username = form.username.data
    email = form.email.data
    password = form.password.data
    role = form.role.data
    check_account = validate_account(
        username=username, email=email, password=password
    )

    if not check_account["status"]:
        return (
            jsonify(
                {
                    "error": __USER_CREATION_ERROR,
                    "message": check_account["message"],
                    "status": check_account["status-code"],
                }
            ),
            check_account["status-code"],
        )

    if not form.validate():
        if form.username.errors:
            return (
                jsonify(
                    {
                        "error": form.username.errors[0],
                        "status": __RESPONSE_STATUS_422,
                    }
                ),
                __RESPONSE_STATUS_422,
            )
        elif form.email.errors:
            return (
                jsonify(
                    {
                        "error": form.email.errors[0],
                        "status": __RESPONSE_STATUS_422,
                    }
                ),
                __RESPONSE_STATUS_422,
            )
        elif form.password.errors:
            return (
                jsonify(
                    {
                        "error": form.password.errors[0],
                        "status": __RESPONSE_STATUS_422,
                    }
                ),
                __RESPONSE_STATUS_422,
            )
        elif form.role.errors:
            return (
                jsonify(
                    {
                        "error": form.role.errors[0],
                        "status": __RESPONSE_STATUS_422,
                    }
                ),
                __RESPONSE_STATUS_422,
            )

    elif form.validate():
        # Check that a user with same email dose not already exist
        user = GwUser.get_by_email(email)
        if user:
            return (
                jsonify(
                    {
                        "error": __USER_WITH_EMAIL_ALREADY_EXISTS,
                        "status": __RESPONSE_STATUS_422,
                    }
                ),
                __RESPONSE_STATUS_422,
            )
        else:
            user = GwUser(username=username, email=check_account["email"])
            user.set_password(password)
            user.save()

            GwUser.add_role_to_user_by_id(user.id, role)

            login_user(user, remember=True)

            # creation of JWT
            activation_token = generate_activation_token(
                SECRET_KEY, SECURITY_PASSWORD_SALT, user.email
            )
            user.last_activation_token = activation_token

            # TODO: send the email to user for account activation.

            jwt_token = initiate_session_jwt(
                {
                    JWT_ENCODING_PARAM_1: user.id,
                    JWT_ENCODING_PARAM_3: user.email,
                    JWT_ENCODING_PARAM_2: user.roles,
                }
            )

        return (
            jsonify(
                {
                    "data": {
                        "user": encode_as_base64(
                            jwt_token[JWT_ENCODING_PARAM_1]
                        ),
                        "jwt": jwt_token,
                    },
                    "status": __RESPONSE_STATUS_200,
                    "message": __SIGNUP_SUCCESSFUL,
                }
            ),
            __RESPONSE_STATUS_200,
        )


@users_bp.route("/confirm/<token>")
def confirm_email(token):
    """Define the endpoint for validating and activating a user account.

    Args:
        token (str): The one time use token to activate a user account.

    Returns:
        json: the response.
    """
    json = request.get_json()
    try:
        jwt = json["data"]["jwt"]
        jwt_decoded = decode_jwt(jwt)

        email = confirm_activation_token(
            SECRET_KEY, SECURITY_PASSWORD_SALT, token
        )
        user = GwUser.get_by_id(jwt_decoded[JWT_ENCODING_PARAM_1])

        user_activated = False

        if user.email == email:
            user_activated = GwUser.activate_by_id(
                jwt_decoded[JWT_ENCODING_PARAM_1]
            )

        if user_activated.is_active():
            return (
                jsonify(
                    {
                        "data": {
                            "user": encode_as_base64(
                                jwt_decoded[JWT_ENCODING_PARAM_1]
                            ),
                            "jwt": jwt,
                        },
                        "message": __ACTIVATION_SUCCESSFUL,
                        "status": __RESPONSE_STATUS_200,
                        "error": "",
                    }
                ),
                __RESPONSE_STATUS_200,
            )
        else:
            return (
                jsonify(
                    {
                        "data": {
                            "user": encode_as_base64(
                                jwt_decoded[JWT_ENCODING_PARAM_1]
                            ),
                            "jwt": jwt,
                        },
                        "error": __INVALID_TOKEN_ERROR,
                        "message": __DEMAND_RENEW_ACTIVATION,
                        "status": __RESPONSE_STATUS_403,
                    }
                ),
                __RESPONSE_STATUS_403,
            )
    except Exception as e:
        return (
            jsonify(
                {
                    "data": "",
                    "error": __GENERIC_ERROR,
                    "message": str(e),
                    "status": __RESPONSE_STATUS_422,
                }
            ),
            __RESPONSE_STATUS_422,
        )


@users_bp.route("/resend-confirmation")
def resend_confirmation_email():
    """Define the endpoint to resend a confirmation email with an activation token.

    Returns:
        json: the response.
    """
    json = request.get_json()
    try:
        jwt = json["data"]["jwt"]
        jwt_decoded = decode_jwt(jwt)

        user = GwUser.get_by_id(jwt_decoded[JWT_ENCODING_PARAM_1])

        if not user.is_active():
            activation_token = generate_activation_token(
                SECRET_KEY, SECURITY_PASSWORD_SALT, user.email
            )
            GwUser.reset_activation_token_by_id(
                jwt_decoded[JWT_ENCODING_PARAM_1], activation_token
            )

            # TODO
            # Send email validation via rabbit MQ

            return (
                jsonify(
                    {
                        "data": {
                            "user": encode_as_base64(
                                jwt_decoded[JWT_ENCODING_PARAM_1]
                            ),
                            "jwt": jwt,
                        },
                        "status": __RESPONSE_STATUS_200,
                        "message": __EMAIL_RESENT,
                        "error": "",
                    }
                ),
                __RESPONSE_STATUS_200,
            )

        return (
            jsonify(
                {
                    "data": {
                        "user": encode_as_base64(
                            jwt_decoded[JWT_ENCODING_PARAM_1]
                        ),
                        "jwt": jwt,
                    },
                    "status": __RESPONSE_STATUS_200,
                    "message": __ACCOUNT_ACTIVATED,
                    "error": "",
                }
            ),
            __RESPONSE_STATUS_200,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "data": "",
                    "error": __GENERIC_ERROR,
                    "message": str(e),
                    "status": __RESPONSE_STATUS_422,
                }
            ),
            __RESPONSE_STATUS_422,
        )


@users_bp.route("/login", methods=["GET", "POST"])
def login():
    """Define the form for a user to login."""
    if current_user.is_authenticated:
        return redirect(url_for("blog_post.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_email(form.email.data)
        if user is not None and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get("next")
            if not next_page or urlparse(next_page).netloc != "":
                next_page = url_for("blog_post.index")
            return redirect(next_page)
    return render_template("users/login_form.html", form=form)


@users_bp.route("/logout")
def logout():
    """Log a user out.

    Returns:
        Response: the response to the index page.
    """
    logout_user()
    return redirect(url_for("index"))


@users_bp.route("/admin/users/")
@login_required
@admin_required
def list_users():
    """Describe the view to list all the users."""
    users = User.get_all()
    return render_template("admin/users.html", users=users)
