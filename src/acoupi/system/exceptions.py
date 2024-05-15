"""Custom Exceptions for Acoupi system."""

from typing import Optional

__all__ = [
    "ProgramNotFoundError",
]


class ProgramNotFoundError(Exception):
    """Exception raised when program is not found."""

    def __init__(self, program: str):
        """Initialize ProgramNotFoundError exception."""
        self.program = program


class InvalidProgramError(Exception):
    """Exception raised when a program file is invalid."""

    def __init__(self, program: str):
        """Initialize InvalidProgramError exception."""
        self.program = program


class ParameterError(Exception):
    """Exception raised when a parameter is invalid."""

    def __init__(self, value: str, message: str, help: Optional[str] = None):
        """Initialize ParameterError exception.

        Parameters
        ----------
        value : str
            The value that caused the error.
        message : str
            The error message.
        help : str, optional
            An optional help message on how to fix the error.
        """
        self.value = value
        self.message = message
        self.help = help

    def __str__(self):
        """Return the error message."""
        return self.message


class HealthCheckError(Exception):
    """Exception raised when a health check fails."""

    def __init__(self, message: str):
        """Initialize HealthError exception."""
        self.message = message

    def __str__(self):
        """Return the error message."""
        return self.message


class DeploymentError(Exception):
    """Exception raised when a deployment fails."""

    def __init__(self, message: str):
        """Initialize DeploymentError exception."""
        self.message = message

    def __str__(self):
        """Return the error message."""
        return self.message
