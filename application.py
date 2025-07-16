"""Define the entry point of the application."""

import os

from core import create_app

settings_module = os.getenv("APP_SETTINGS_MODULE")
print("settings_module = {}".format(settings_module))
app = create_app(settings_module)
print("The application is running.")
