"""Verify email format and validity."""

from email_validator import EmailNotValidError, validate_email


class EmailValidator:
    """Describe the emails validation."""

    @staticmethod
    def is_valid_email(email: str):
        """Validate an email.

        Args:
            email (str): the email to validate.

        Returns:
            dict: status: True if the email is valid, email: the nromalized string for an email.
        """
        if email is None:
            return {"status": False, "message": "", "email": ""}

        try:
            emailinfo = validate_email(email, check_deliverability=True)
            return {
                "status": True,
                "message": "",
                "email": emailinfo.normalized,
            }

        except EmailNotValidError as e:
            return {"status": False, "message": str(e), "email": ""}
