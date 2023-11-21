"""Custom Exceptions for Acoupi system."""


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
