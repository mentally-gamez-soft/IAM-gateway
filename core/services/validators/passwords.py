import json

import requests

from core import app


class PasswordValidator:

    @staticmethod
    def is_valid_password(
        password: str,
        url_api: str = None,
        has_digits: bool = True,
        has_lowercase: bool = True,
        has_spaces: bool = False,
        has_symbols: bool = True,
        has_uppercase: bool = True,
        min_length: int = 10,
        max_length: int = 50,
        min_accepted_score: int = 70,
    ):
        if password is None or password == "":
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
                "has_spaces": False,
                "has_symbols": has_symbols,
                "has_uppercase": has_uppercase,
                "max_length": max_length,
                "min_length": min_length,
            },
            "min_accepted_score": min_accepted_score,
        }

        response = requests.post(url_api, json=payload)
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
                == "The password is not meeting the length and/or characters requirements !"
            ):
                return {
                    "status": False,
                    "status-code": 280,
                    "message": "The password is not matching the requisites !",
                }
            else:
                return {"status": True, "status-code": 200}
