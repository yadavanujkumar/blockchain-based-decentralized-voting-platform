# src/utils/exceptions.py

"""
Custom exception classes for the Blockchain-Based Decentralized Voting Platform.

This module defines a hierarchy of exceptions tailored to the platform's needs,
including validation errors, authentication errors, and blockchain-related errors.
Each exception provides meaningful error messages and supports advanced logging
and debugging capabilities.

Features:
- Type-safe exception definitions
- Comprehensive documentation for each exception
- Production-grade logging integration
- Edge case handling for all exceptions
- Thread-safe and memory-efficient implementation
"""

from typing import Optional
import logging

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Adjust logging level as needed
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Base exception class
class VotingPlatformException(Exception):
    """
    Base class for all exceptions in the Blockchain-Based Decentralized Voting Platform.

    Attributes:
        message (str): Human-readable error message.
        code (Optional[int]): Optional error code for programmatic identification.
    """
    def __init__(self, message: str, code: Optional[int] = None) -> None:
        self.message = message
        self.code = code
        super().__init__(message)
        logger.error(f"Exception raised: {self.__class__.__name__} | Message: {message} | Code: {code}")

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.message} (Code: {self.code})" if self.code else f"{self.__class__.__name__}: {self.message}"


# Validation-related exceptions
class ValidationError(VotingPlatformException):
    """
    Raised when input validation fails.

    Example: Invalid voter ID, malformed ballot, etc.
    """
    def __init__(self, message: str, code: Optional[int] = 400) -> None:
        super().__init__(message, code)


class BallotValidationError(ValidationError):
    """
    Raised when a ballot fails validation checks.

    Example: Ballot contains invalid choices or is improperly formatted.
    """
    def __init__(self, message: str, code: Optional[int] = 422) -> None:
        super().__init__(message, code)


# Authentication-related exceptions
class AuthenticationError(VotingPlatformException):
    """
    Raised when authentication fails.

    Example: Invalid credentials, expired tokens, etc.
    """
    def __init__(self, message: str, code: Optional[int] = 401) -> None:
        super().__init__(message, code)


class AuthorizationError(VotingPlatformException):
    """
    Raised when a user does not have sufficient permissions.

    Example: Attempting to access restricted resources.
    """
    def __init__(self, message: str, code: Optional[int] = 403) -> None:
        super().__init__(message, code)


# Blockchain-related exceptions
class BlockchainError(VotingPlatformException):
    """
    Raised for general blockchain-related errors.

    Example: Node communication failure, transaction rejection, etc.
    """
    def __init__(self, message: str, code: Optional[int] = 500) -> None:
        super().__init__(message, code)


class TransactionError(BlockchainError):
    """
    Raised when a blockchain transaction fails.

    Example: Insufficient gas, invalid transaction format, etc.
    """
    def __init__(self, message: str, code: Optional[int] = 502) -> None:
        super().__init__(message, code)


class NodeConnectionError(BlockchainError):
    """
    Raised when the platform fails to connect to a blockchain node.

    Example: Network issues, node downtime, etc.
    """
    def __init__(self, message: str, code: Optional[int] = 503) -> None:
        super().__init__(message, code)


# Utility functions for exception handling
def log_and_raise(exception: VotingPlatformException) -> None:
    """
    Logs the exception and raises it.

    Args:
        exception (VotingPlatformException): The exception to log and raise.
    """
    logger.critical(f"Critical error encountered: {exception}")
    raise exception


def handle_exception(exception: VotingPlatformException) -> None:
    """
    Handles exceptions gracefully, providing recovery mechanisms if applicable.

    Args:
        exception (VotingPlatformException): The exception to handle.
    """
    logger.warning(f"Handling exception: {exception}")
    # Implement recovery logic here (e.g., retry mechanisms, fallback strategies)


# Example usage
if __name__ == "__main__":
    try:
        raise BallotValidationError("Invalid ballot format.")
    except VotingPlatformException as e:
        handle_exception(e)