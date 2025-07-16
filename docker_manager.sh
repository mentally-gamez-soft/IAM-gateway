#!/bin/bash
. $HOME/.profile;

# Function to set the environment to work on.
# Outputs the environement dev or prod
set_environment () {
    # Ask the user for the environment
    read -p "Please indicate on which environment you want to work on ? [dev, prod]: " chosen_env

    chosen_env=$(echo "$chosen_env" | tr '[:upper:]' '[:lower:]');

    if [[ "$chosen_env" != "dev" && "$chosen_env" != "prod" ]]; then
        echo "Error - The chosen environment is invalid !";
        exit 10;
    fi;

    echo "$chosen_env";
    return 0;
}

# Function to get the current name of the application.
# Outputs the name of the application.
get_current_app_name () {
    curr_app_name=`head -1 Docker/application/$1/app.name.env | cut -d'=' -f2`;
    echo "$curr_app_name";
    return 0;
}

# Function to set the new name of the application.
# Outputs the new name of the application.
set_application_name () {
    # Ask the user to give a name to the application
    read -p "Please indicate the name for this application: " new_app_name

    if [[ "$new_app_name" == "" ]]; then
        new_app_name="$1";
    fi;

    echo "APP_NAME=${new_app_name}" > Docker/application/$2/app.name.env;

    echo "$new_app_name";
    return 0;
}

# Function to get the current version of the application.
# Outputs the vrsion of the application.
get_current_app_version () {
    curr_app_version=`head -1 Docker/application/$1/app.version.env | cut -d'=' -f2`;
    echo "$curr_app_version";
    return 0;
}

# Function to set the new version of the application.
# Outputs the new version of the application.
set_application_version () {
    # Ask the user for the version of the app
    read -p "Please indicate the new version of the application (eg: 0.3.1f) for the environment $1 " new_version_number

    VERSION_PATTERN="^[0-9]\.[0-9]\.[0-9][a-zA-Z]$"

    # check the version number with the pattern
    if ! [[ "$new_version_number" =~ $VERSION_PATTERN ]]; then
    echo "Error - The input version number is invalid!";
        exit 20;
    fi; 

    echo "APP_VERSION=${new_version_number}" > Docker/application/$1/app.version.env;

    echo "$new_version_number";
    return 0;
}

# Function to create a docker image
create_docker_image () { 
    # Ask the user on which environement to work
    ENVIRONMENT=$(set_environment);
    echo "You chose to work on ${ENVIRONMENT} environment.";

    # Show the current name of the application:
    CURRENT_APP_NAME=$(get_current_app_name $ENVIRONMENT);
    echo "The application name is currently $CURRENT_APP_NAME for the environment ${ENVIRONMENT}.";

    # Change the name of the application
    APPLICATION_NAME=$(set_application_name ${CURRENT_APP_NAME} ${ENVIRONMENT})
    echo "The application is now named: ${APPLICATION_NAME} for the environment ${ENVIRONMENT}.";


    # Show the current version of the image:
    CURRENT_VERSION_NUMBER=$(get_current_app_version ${ENVIRONMENT});
    echo "The application is currently based on image version number ${CURRENT_VERSION_NUMBER} for the environment ${ENVIRONMENT}";

    # Ask the user for the version of the app
    VERSION_NUMBER=$(set_application_version ${ENVIRONMENT});
    echo "The application version number env file has been updated (Docker/application/${ENVIRONMENT}/app.version.env).";

    export APP_VERSION="$VERSION_NUMBER";
    export APP_ENV="$ENVIRONMENT";
    export APP_NAME="$APPLICATION_NAME";

    docker compose -f Docker/application/${ENVIRONMENT}/docker-compose-${ENVIRONMENT}.yaml build 
    #--build-arg DOCKERREPOSITORY=${DOCKERREPOSITORY}
}

# Function to execute a container
execute_docker_image () {
    # Ask the user on which environement to work
    ENVIRONMENT=$(set_environment);
    echo "You chose to work on ${ENVIRONMENT} environment.";

    # Get the name of the application:
    CURRENT_APP_NAME=$(get_current_app_name $ENVIRONMENT);
    echo "The application name is currently $CURRENT_APP_NAME for the environment ${ENVIRONMENT}.";

    # Get the current version of the image:
    CURRENT_VERSION_NUMBER=$(get_current_app_version ${ENVIRONMENT});
    echo "The application is currently based on image version number ${CURRENT_VERSION_NUMBER} for the environment ${ENVIRONMENT}";

   export APP_VERSION="$CURRENT_VERSION_NUMBER";
   export APP_ENV="$ENVIRONMENT";
   export APP_NAME="$CURRENT_APP_NAME";

    # Run the container
    # docker compose --env-file Docker/application/${ENVIRONMENT}/.env --env-file Docker/application/${ENVIRONMENT}/app.name.env --env-file Docker/application/${ENVIRONMENT}/app.version.env -f Docker/application/${ENVIRONMENT}/docker-compose-${ENVIRONMENT}.yaml up 
    docker compose -f Docker/application/${ENVIRONMENT}/docker-compose-${ENVIRONMENT}.yaml up 
}

# Function to stop a container
stop_docker_image () {
    # Ask the user on which environement to work
    ENVIRONMENT=$(set_environment);
    echo "You chose to work on ${ENVIRONMENT} environment.";

    # Get the name of the application:
    CURRENT_APP_NAME=$(get_current_app_name $ENVIRONMENT);
    echo "The application name is currently $CURRENT_APP_NAME for the environment ${ENVIRONMENT}.";

    # Get the current version of the image:
    CURRENT_VERSION_NUMBER=$(get_current_app_version ${ENVIRONMENT});
    echo "The application is currently based on image version number ${CURRENT_VERSION_NUMBER} for the environment ${ENVIRONMENT}";

   export APP_VERSION="$CURRENT_VERSION_NUMBER";
   export APP_ENV="$ENVIRONMENT";
   export APP_NAME="$CURRENT_APP_NAME";

    # Run the container
    docker compose --env-file Docker/application/${ENVIRONMENT}/.env --env-file Docker/application/${ENVIRONMENT}/app.name.env --env-file Docker/application/${ENVIRONMENT}/app.version.env  -f Docker/application/${ENVIRONMENT}/docker-compose-${ENVIRONMENT}.yaml down 
}

# ============================ MAIN PROGRAM ====================================================
while true; do 
    # clear the screen
    clear 

    echo "------------------------------------------------------------------------------------------"
    echo "                 Manager for the docker images of the application                         "
    echo "------------------------------------------------------------------------------------------"
    echo " 1. Create a new docker image"
    echo " 2. Run a docker container"
    echo " 3. Stop a docker container"
    echo " 4. Exit"
    echo "------------------------------------------------------------------------------------------"

    # Prompt user for the choice
    read -p "Enter your choice (1-4): " choice

    case "$choice" in 
        1) 
            echo -e "\n --- Creation of a new image docker ---"
            create_docker_image
            echo -e "\n -------------------------------"
            ;;

        2) 
            echo -e "\n --- Execution of a container ---"
            execute_docker_image
            echo -e "\n --------------------------------"
            ;;
        3) 
            echo -e "\n --- Stop of a container ---"
            stop_docker_image
            echo -e "\n --------------------------------"
            ;;

        4) 
            echo -e "\n All done. See you soon!"
            break
            ;;

        *) 
            echo -e "\n Invalid option! Please enter a number between 1 and 4."
            ;;
    esac

    read -n 1 -s -r -p "Press any key to continue..."
    echo
done