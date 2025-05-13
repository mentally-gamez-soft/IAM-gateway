"""Define the entry point of the application."""

import os

from core import create_app

settings_module = os.getenv("APP_SETTINGS_MODULE")


def main():
    """Describe the entry point of the program."""
    app = create_app(settings_module)


if __name__ == "__main__":
    main()
