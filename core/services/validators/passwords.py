"""Define the module for validating the passwords."""

import json

import requests

from core import app


class PasswordValidator:
    """Declare the validator for the password."""

    @staticmethod
    def is_valid_password(
        url_api: str,
        password: str,
        has_digits: bool = True,
        has_lowercase: bool = True,
        has_spaces: bool = False,
        has_symbols: bool = True,
        has_uppercase: bool = True,
        min_length: int = 10,
        max_length: int = 50,
        min_accepted_score: int = 70,
    ):
        """Define the validator parameters for the passwords.

        Args:
            url_api (str): The API call to the external ws password scoring.
            password (str): the password to score.
            has_digits (bool, optional): indicate if the password should have ate least one digit. Defaults to True.
            has_lowercase (bool, optional): indicate if the password should have at least one lowercase character. Defaults to True.
            has_spaces (bool, optional): indicate if the password should have at least one space character. Defaults to False.
            has_symbols (bool, optional): indicate if the password should have at least one special symbol character. Defaults to True.
            has_uppercase (bool, optional): indicate if the password should have at least one uppercase character. Defaults to True.
            min_length (int, optional): indicate the minimum length characters for a password valid. Defaults to 10.
            max_length (int, optional): indicate the maximum length characters for a valid password. Defaults to 50.
            min_accepted_score (int, optional): indicate the minimum a valid score of a password. Defaults to 70.

        Returns:
            _type_: _description_
        """
        if (
            password is None
            or password
            == ""  # nosec - there is no hardcoded password, just a value control.
        ):
            return {
                "status": False,
                "status-code": 270,
                "message": "The password is empty !",
            }

        url_api = app.config["API_PWD"]

        payload = {
            "password": password,
            "characteristics": {
                "has_digits": has_digits,
                "has_lowercase": has_lowercase,
                "has_spaces": has_spaces,
                "has_symbols": has_symbols,
                "has_uppercase": has_uppercase,
                "max_length": max_length,
                "min_length": min_length,
            },
            "min_accepted_score": min_accepted_score,
        }

        response = requests.post(url_api, json=payload, timeout=5)
        status_code = response.status_code
        message = json.loads(response.text)

        if status_code != 200:
            return {
                "status": False,
                "status-code": status_code,
                "message": "The password is not valid !",
            }

        else:
            if (
                message.get("message_score")
                == "The strength of the password is too low !"
            ):
                return {
                    "status": False,
                    "status-code": 290,
                    "message": "The password is too weak !",
                }
            elif (
                message.get("message_password")
                == "The password is not meeting the length and/or characters"
                " requirements !"
            ):
                return {
                    "status": False,
                    "status-code": 280,
                    "message": "The password is not matching the requisites !",
                }
            else:
                return {"status": True, "status-code": 200}
