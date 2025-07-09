"""Configure the swagger documentation of the api."""

from flask_swagger_ui import get_swaggerui_blueprint

SWAGGER_URL = "/swagger"
API_URL = "/static/swagger-docs/swagger.json"

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        "app_name": "webservice .",
        "layout": "BaseLayout",
        "withCredentials": True,
        # https://stackoverflow.com/questions/78413504/swaggers-requestinterceptor-with-python-fast-api
        "requestInterceptor": """
                            (req) => {
                                // Modify the request object as needed
                                req.headers['X-CSRF-TOKEN'] = '<your CSRFToken here>';
                                return req;
                            }
                        """,
        # "docExpansion": "none",
    },
)
