# IAM-gateway
gateway portal for users login/logout
and discovery service

The web service is ready for executing in the following environment:
- local development
- containerized docker host development
- containerized docker host production ready (gunicorn and nginx)

A set of tools is provided to help you to create, run and stop the docker container.

## Requirements
- Python 3.11 or higher
- pip 24.0 or higher
- virtualenv 20.16.7 or higher
- uv 0.4.0 or higher
- docker 20.10.21 or higher
- docker-compose 1.29.2 or higher

## Stack Technologies
![Alt text](technology_stack_IAM-GW.svg)

## API Endpoints
### Sanity check
    The check is located at home "/"

### Signup
    The transations endpoint is located at "/signup"

### Login
    The transations endpoint is located at "/login"

### Logout
    The transations endpoint is located at "/logout"

### Swagger documentations
    The swagger UI is located at "/swagger"

## Display environment variables
    display all env variables:
    gci env:* | sort-object name

## Set the environment variables

    On unix OS:
     - export FLASK_APP="application"
     - export FLASK_ENV="development"
     - export APP_SETTINGS_MODULE="config.local"
     - export FLASK_DEBUG=1

    On Windows OS powershell:
     - $env:FLASK_APP="application"
     - $env:FLASK_ENV="development"
     - $env:APP_SETTINGS_MODULE="config.local"
     - $env:FLASK_DEBUG = "1"

## Running application
## Local development

    uv run -m flask --app application run --port 3456 --host 0.0.0.0

### Executing the tests suit
    uv run -m unittest tests.test_standard_routes

## Docker Images
### Create an image
    On unix OS:
    execute the shell ./docker_manager.sh choose option (1) and follow the instructions.

    On windows OS:
    execute the shell ./docker_manager.ps1 choose option (1) and follow the instructions.

### Run a container
    On unix OS:
    execute the shell ./docker_manager.sh choose option (2) and follow the instructions.

    On windows OS:
    execute the shell ./docker_manager.ps1 choose option (2) and follow the instructions.

### Stop a container
    On unix OS:
    execute the shell ./docker_manager.sh choose option (3) and follow the instructions.

    On windows OS:
    execute the shell ./docker_manager.ps1 choose option (3) and follow the instructions.
