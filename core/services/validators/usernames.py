from python_usernames import is_safe_username


class UsernameValidator:

    @staticmethod
    def is_valid_username(username: str, max_length: int = 30) -> bool:
        return is_safe_username(username, max_length=max_length)
