import os

from core import create_app


def main():
    app = create_app(settings_module)


settings_module = os.getenv("APP_SETTINGS_MODULE")

if __name__ == "__main__":
    main()
