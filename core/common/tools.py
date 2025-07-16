"""Define all the helpers and tools in this module."""

def get_duration_in_seconds(duration: int, unit: str = "SECONDS") -> int:
    """Get the equivalent duration in seconds from the parameters input.

    Args:
        duration (int): the duration to translate.
        unit (str, optional): The unit for the duration input SECONDS, MINUTES, HOURS, DAYS. Defaults to "SECONDS".

    Returns:
        int: The equivalented duration in seconds.
    """
    if "SECONDS" == unit.upper():
        return duration
    elif "MINUTES" == unit.upper():
        return duration * 60
    elif "HOURS" == unit.upper():
        return duration * 3600
    elif "DAYS" == unit.upper():
        return duration * 24 * 3600


def get_duration_in_minutes(duration: int, unit: str = "SECONDS") -> int:
    """Get the equivalent duration in minutes from the parameters input.

    Args:
        duration (int): the duration to translate.
        unit (str, optional): The unit for the duration input SECONDS, MINUTES, HOURS, DAYS. Defaults to "SECONDS".

    Returns:
        int: The equivalented duration in minutes.
    """
    if "SECONDS" == unit.upper():
        return int(duration / 60)
    elif "MINUTES" == unit.upper():
        return duration
    elif "HOURS" == unit.upper():
        return duration * 60
    elif "DAYS" == unit.upper():
        return duration * 24 * 60
