

function Set-Environment {
    # Ask the user for the environment
    $environment = Read-Host "Please indicate on which environment you want to work on ? [dev, prod]: "

    # Define the allowed environements
    $allowedEnvironments = "dev", "prod"

    if ($allowedEnvironments -notcontains $environment) {
        # If the name is not allowed, throw a terminating error
        throw "Error: The envir '$environment' is not allowed. Please enter dev or prod."
    }
    if ([string]::IsNullOrWhiteSpace($environment)) {
        throw "Error: The environment cannot be empty or just spaces. Please provide a valid environment to work on."
    }

    # Return the name that was just entered by the user
    return $environment
}

function Get-AppNameFromEnvFile {
    param (
        [Parameter(Mandatory=$true)] # This makes the -Environment parameter required
        [string]$Environment
    )

    # Construct the path dynamically using the provided Environment parameter
    $envFilePath = "./Docker/application/$Environment/app.name.env"

    # Check if the file exists before attempting to read it
    if (-not (Test-Path $envFilePath -PathType Leaf)) {
        throw "Error: The app.name.env file was not found at '$envFilePath'."
    }

    # Read the first line of the file
    $firstLine = Get-Content -Path $envFilePath -TotalCount 1

    # Define the expected prefix for the variable
    $prefix = "APP_NAME="

    # Check if the first line starts with the expected prefix
    if ($firstLine.StartsWith($prefix)) {
        # Extract the value by removing the prefix
        $appName = $firstLine.Substring($prefix.Length)
        return $appName
    } else {
        # If the first line doesn't match the expected format
        throw "Error: The first line of the app.name.env file does not contain 'APP_NAME=' in the expected format. Found: '$firstLine'"
    }
}

function Set-AppName {
    param (
        [Parameter(Mandatory=$true)] # This makes the -Environment parameter required
        [string]$Environment
    )

    # Ask the user for the environment
    $appname = Read-Host "Please indicate the name for this application: "

    if ([string]::IsNullOrWhiteSpace($appname)) {
        throw "Error: The application name cannot be empty or just spaces. Please provide a valid name for this application."
    }

    # Construct the full path to the target file
    $targetDirectory = "./Docker/application/$Environment"
    $targetFilePath = Join-Path -Path $targetDirectory -ChildPath "app.name.env"

    # Ensure the target directory exists
    if (-not (Test-Path $targetDirectory -PathType Container)) {
        Write-Host "Creating directory: $targetDirectory" -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null
    }

    # Construct the content line to be written to the file
    $fileContent = "APP_NAME=$appname"

    # Write the content to the file (this will overwrite existing content)
    try {
        Set-Content -Path $targetFilePath -Value $fileContent
        Write-Host "Successfully set application name to '$appname' in '$targetFilePath'." -ForegroundColor Green
    }
    catch {
        throw "Error writing to file '$targetFilePath': $($_.Exception.Message)"
    }

    # Return the name that was just entered by the user
    return $appname
}

function Get-AppVersionFromEnvFile {
    param (
        [Parameter(Mandatory=$true)] # This makes the -Environment parameter required
        [string]$Environment
    )

    # Construct the path dynamically using the provided Environment parameter
    $envFilePath = "./Docker/application/$Environment/app.version.env"

    # Check if the file exists before attempting to read it
    if (-not (Test-Path $envFilePath -PathType Leaf)) {
        throw "Error: The app.version.env file was not found at '$envFilePath'."
    }

    # Read the first line of the file
    $firstLine = Get-Content -Path $envFilePath -TotalCount 1

    # Define the expected prefix for the variable
    $prefix = "APP_VERSION="

    # Check if the first line starts with the expected prefix
    if ($firstLine.StartsWith($prefix)) {
        # Extract the value by removing the prefix
        $appName = $firstLine.Substring($prefix.Length)
        return $appName
    } else {
        # If the first line doesn't match the expected format
        throw "Error: The first line of the .env file does not contain 'APP_VERSION=' in the expected format. Found: '$firstLine'"
    }
}

function Set-AppVersion {
    param (
        [Parameter(Mandatory=$true)] # The environment (e.g., "dev", "prod") is required
        [string]$Environment
    )

    # 1. Prompt the user for the new application version
    $newAppVersion = Read-Host "Please enter the new application version (e.g., 1.2.3a) for the '$Environment' environment"

    # --- Input Validation for Version Pattern and Empty String ---
    # Regex pattern:
    # ^             - Start of the string
    # \d{1}         - Exactly one digit
    # \.            - A literal dot (needs to be escaped with \)
    # \d{1}         - Exactly one digit
    # \.            - A literal dot
    # \d{1}         - Exactly one digit
    # [a-zA-Z]{1}   - Exactly one letter (uppercase or lowercase)
    # $             - End of the string
    $versionPattern = "^\d{1}\.\d{1}\.\d{1}[a-zA-Z]{1}$"

    if ([string]::IsNullOrWhiteSpace($newAppVersion)) {
        throw "Error: The application version cannot be empty or just spaces. Please provide a valid version."
    } elseif ($newAppVersion -notmatch $versionPattern) {
        throw "Error: The version '$newAppVersion' does not match the required pattern (e.g., 1.2.3a). Please ensure it's 'digit.digit.digit.letter'."
    }
    # -------------------------------------------------------------

    # Construct the full path to the target file (assuming a similar naming convention as app.name.env)
    $targetDirectory = "./Docker/application/$Environment"
    $targetFilePath = Join-Path -Path $targetDirectory -ChildPath "app.version.env" # New file name

    # Ensure the target directory exists
    if (-not (Test-Path $targetDirectory -PathType Container)) {
        Write-Host "Creating directory: $targetDirectory" -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null
    }

    # Construct the content line to be written to the file
    $fileContent = "APP_VERSION=$newAppVersion"

    # Write the content to the file (this will overwrite existing content)
    try {
        Set-Content -Path $targetFilePath -Value $fileContent
        Write-Host "Successfully set application version to '$newAppVersion' in '$targetFilePath'." -ForegroundColor Green
    }
    catch {
        throw "Error writing to file '$targetFilePath': $($_.Exception.Message)"
    }

    # Return the new app version
    return $newAppVersion
}

function Create-Docker-Image {
    # Ask the user on which environment to work
    $ENVIRONMENT = Set-Environment
    Write-Host "You chose to work on '$ENVIRONMENT' environment."

    # Show the current name of the application:
    $CURRENT_APP_NAME = Get-AppNameFromEnvFile -Environment $ENVIRONMENT 
    Write-Host "The application name is currently '$CURRENT_APP_NAME' for the environment '$ENVIRONMENT'."

    # Change the name of the application
    $APPLICATION_NAME = Set-AppName -Environment $ENVIRONMENT 
    Write-Host  "The application is now named: '$APPLICATION_NAME' for the environment '$ENVIRONMENT'."

    # Show the current version of the image:
    $CURRENT_VERSION_NUMBER = Get-AppVersionFromEnvFile -Environment $ENVIRONMENT 
    Write-Host "The application is currently based on image version number '$CURRENT_VERSION_NUMBER' for the environment '$ENVIRONMENT'"

    # Ask the user for the version of the app
    $VERSION_NUMBER = Set-AppVersion -Environment $ENVIRONMENT 
    Write-Host "The application version number env file has been updated (Docker/application/$ENVIRONMENT/app.version.env)."

    $Env:APP_VERSION="$VERSION_NUMBER"
    $Env:APP_ENV="$ENVIRONMENT"
    $Env:APP_NAME="$APPLICATION_NAME"

    docker compose -f Docker/application/$ENVIRONMENT/docker-compose-$ENVIRONMENT.yaml build
}

function Execute-Docker-Image {
    # Ask the user on which environment to work
    $ENVIRONMENT = Set-Environment
    Write-Host "You chose to work on '$ENVIRONMENT' environment."

    # Show the current name of the application:
    $CURRENT_APP_NAME = Get-AppNameFromEnvFile -Environment $ENVIRONMENT 
    Write-Host "The application name is currently '$CURRENT_APP_NAME' for the environment '$ENVIRONMENT'."

     # Show the current version of the image:
    $CURRENT_VERSION_NUMBER = Get-AppVersionFromEnvFile -Environment $ENVIRONMENT 
    Write-Host "The application is currently based on image version number '$CURRENT_VERSION_NUMBER' for the environment '$ENVIRONMENT'"

    $Env:APP_VERSION="$CURRENT_VERSION_NUMBER";
    $Env:APP_ENV="$ENVIRONMENT";
    $Env:APP_NAME="$CURRENT_APP_NAME";

    # Run the container
    docker compose -f Docker/application/$ENVIRONMENT/docker-compose-$ENVIRONMENT.yaml up 
}

function Stop-Docker-Image {
    # Ask the user on which environment to work
    $ENVIRONMENT = Set-Environment
    Write-Host "You chose to work on '$ENVIRONMENT' environment."

    # Show the current name of the application:
    $CURRENT_APP_NAME = Get-AppNameFromEnvFile -Environment $ENVIRONMENT 
    Write-Host "The application name is currently '$CURRENT_APP_NAME' for the environment '$ENVIRONMENT'."

     # Show the current version of the image:
    $CURRENT_VERSION_NUMBER = Get-AppVersionFromEnvFile -Environment $ENVIRONMENT 
    Write-Host "The application is currently based on image version number '$CURRENT_VERSION_NUMBER' for the environment '$ENVIRONMENT'"

    $Env:APP_VERSION="$CURRENT_VERSION_NUMBER";
    $Env:APP_ENV="$ENVIRONMENT";
    $Env:APP_NAME="$CURRENT_APP_NAME";

    # Run the container
    docker compose --env-file Docker/application/$ENVIRONMENT/.env --env-file Docker/application/$ENVIRONMENT/app.name.env --env-file Docker/application/$ENVIRONMENT/app.version.env   -f Docker/application/$ENVIRONMENT/docker-compose-$ENVIRONMENT.yaml down 
}

function Get-IntegerInput {
    param (
        [Parameter(Mandatory=$true)]
        [string]$PromptMessage
    )
    $inputNumber = $null
    do {
        $inputString = Read-Host $PromptMessage
        if ([string]::IsNullOrWhiteSpace($inputString)) {
            Write-Warning "Input cannot be empty. Please enter an integer."
            continue
        }
        if (-not ([int]::TryParse($inputString, [ref]$inputNumber))) {
            Write-Warning "Invalid input. Please enter a valid integer."
        }
    } while (-not ([int]::TryParse($inputString, [ref]$inputNumber)))
    return $inputNumber
}

# --- Main Program Menu ---
function Show-MainMenu {
    Write-Host "`n------------------------------------------------------------------------------------------"
    Write-Host "                 Manager for the docker images of the application                         "
    Write-Host "------------------------------------------------------------------------------------------"
    Write-Host " 1. Create a new docker image"
    Write-Host " 2. Run a docker container"
    Write-Host " 3. Stop a docker container"
    Write-Host " 4. Exit"
    Write-Host "------------------------------------------------------------------------------------------"
}

$choice = 0
do {
    Show-MainMenu
    $menuChoice = Read-Host "Please enter your choice (1-4)"

    # Attempt to convert choice to integer, default to 0 if not valid
    if (-not ([int]::TryParse($menuChoice, [ref]$choice))) {
        $choice = 0 # Set to an invalid choice to trigger the loop again
    }

    switch ($choice) {
        1 {
            Write-Host "`n--- Creation of a new image docker ---"
            Create-Docker-Image
            Write-Host "`n -------------------------------"
        }
        2 {
            Write-Host "`n --- Execution of a container ---"
            Execute-Docker-Image
            Write-Host "`n --------------------------------"
        }
        3 {
            Write-Host "`n --- Stop of a container ---"
            Stop-Docker-Image 
            Write-Host "`n --------------------------------"

        }
        4 {
            Write-Host "`nExiting the program. Goodbye!" -ForegroundColor Yellow
        }
        Default {
            Write-Warning "Invalid choice. Please enter 1, 2, 3 or 4."
        }
    }
} while ($choice -ne 4)


Show-MainMenu