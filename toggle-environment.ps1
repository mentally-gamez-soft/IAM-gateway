Write-Host "===============================================================================================================================";
Write-Host "===================== { CURRENT ENVIRONMENT   --> $env:APP_SETTINGS_MODULE } ==================================================";
Write-Host "===============================================================================================================================";

function Format-Color([hashtable] $Colors = @{}, [switch] $SimpleMatch) {
    $lines = ($input | Out-String) -replace "`r", "" -split "`n"
    foreach($line in $lines) {
        $color = ''
        foreach($pattern in $Colors.Keys){
            if(!$SimpleMatch -and $line -match $pattern) { $color = $Colors[$pattern] }
            elseif ($SimpleMatch -and $line -like $pattern) { $color = $Colors[$pattern] }
        }
        if($color) {
            Write-Host -ForegroundColor $color $line
        } else {
            Write-Host $line
        }
    }
}
Function Read-YesNoChoice {
    <#
        .SYNOPSIS
        Prompt the user for a Yes No choice.

        .DESCRIPTION
        Prompt the user for a Yes No choice and returns 0 for no and 1 for yes.

        .PARAMETER Title
        Title for the prompt

        .PARAMETER Message
        Message for the prompt
        
        .PARAMETER DefaultOption
        Specifies the default option if nothing is selected

        .INPUTS
        None. You cannot pipe objects to Read-YesNoChoice.

        .OUTPUTS
        Int. Read-YesNoChoice returns an Int, 0 for no and 1 for yes.

        .EXAMPLE
        PS> $choice = Read-YesNoChoice -Title "Please Choose" -Message "Yes or No?"
        
        Please Choose
        Yes or No?
        [N] No  [Y] Yes  [?] Help (default is "N"): y
        PS> $choice
        1
        
        .EXAMPLE
        PS> $choice = Read-YesNoChoice -Title "Please Choose" -Message "Yes or No?" -DefaultOption 1
        
        Please Choose
        Yes or No?
        [N] No  [Y] Yes  [?] Help (default is "Y"):
        PS> $choice
        1

        .LINK
        Online version: https://www.chriscolden.net/2024/03/01/yes-no-choice-function-in-powershell/
    #>
    
    Param (
        [Parameter(Mandatory=$true)][String]$Title,
        [Parameter(Mandatory=$true)][String]$Message,
        [Parameter(Mandatory=$false)][Int]$DefaultOption = 0
    )
    
    $No = New-Object System.Management.Automation.Host.ChoiceDescription '&No', 'No'
    $Yes = New-Object System.Management.Automation.Host.ChoiceDescription '&Yes', 'Yes'
    $Options = [System.Management.Automation.Host.ChoiceDescription[]]($No, $Yes)
    
    return $host.ui.PromptForChoice($Title, $Message, $Options, $DefaultOption)
}

$choice = Read-YesNoChoice -Title "Change the current environment? [$env:APP_SETTINGS_MODULE]" -Message "Would you like to change environment ? (y/n)"

switch($choice)
{
    # No
    0 {
        Write-Host "You chose to keep it that way.";
    }
    # Yes
    1 {
        echo "You are now using the following environment:"  | Format-Color @{ 'local' = 'Blue' };

        if($env:APP_SETTINGS_MODULE -eq 'config.local') {
            echo "testing" | Format-Color @{ 'testing' = 'Cyan' };
            $env:APP_SETTINGS_MODULE = 'config.testing';
        }
        else {
            echo "local" | Format-Color @{ 'local' = 'Green' };
            $env:APP_SETTINGS_MODULE = 'config.local';
        }
    }
}
Write-Host "===============================================================================================================================";