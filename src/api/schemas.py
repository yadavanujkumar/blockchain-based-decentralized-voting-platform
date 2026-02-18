# src/api/schemas.py

from pydantic import BaseModel, EmailStr, Field, constr, conint, validator
from typing import List, Optional
from datetime import datetime
from uuid import UUID


# Utility Schemas
class AuditSchema(BaseModel):
    created_at: datetime = Field(..., description="Timestamp when the record was created")
    updated_at: datetime = Field(..., description="Timestamp when the record was last updated")
    deleted_at: Optional[datetime] = Field(None, description="Timestamp when the record was soft-deleted")


# User Registration Schema
class UserRegistrationRequest(BaseModel):
    username: constr(min_length=3, max_length=50) = Field(..., description="Unique username for the user")
    email: EmailStr = Field(..., description="Valid email address of the user")
    password: constr(min_length=8, max_length=128) = Field(..., description="Secure password for the user")
    is_admin: bool = Field(False, description="Flag to indicate if the user is an admin")

    @validator("password")
    def validate_password_strength(cls, value):
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in value):
            raise ValueError("Password must contain at least one uppercase letter")
        return value


class UserRegistrationResponse(BaseModel):
    user_id: UUID = Field(..., description="Unique identifier for the registered user")
    username: str = Field(..., description="Username of the registered user")
    email: EmailStr = Field(..., description="Email of the registered user")
    created_at: datetime = Field(..., description="Timestamp of user registration")


# Election Creation Schema
class ElectionCreationRequest(BaseModel):
    title: constr(min_length=5, max_length=100) = Field(..., description="Title of the election")
    description: Optional[str] = Field(None, description="Detailed description of the election")
    start_time: datetime = Field(..., description="Start time of the election")
    end_time: datetime = Field(..., description="End time of the election")
    candidates: List[constr(min_length=3, max_length=50)] = Field(..., min_items=2, description="List of candidate names")

    @validator("end_time")
    def validate_end_time(cls, value, values):
        if "start_time" in values and value <= values["start_time"]:
            raise ValueError("End time must be after start time")
        return value


class ElectionCreationResponse(BaseModel):
    election_id: UUID = Field(..., description="Unique identifier for the created election")
    title: str = Field(..., description="Title of the election")
    created_at: datetime = Field(..., description="Timestamp of election creation")


# Vote Casting Schema
class VoteCastingRequest(BaseModel):
    election_id: UUID = Field(..., description="Unique identifier of the election")
    voter_id: UUID = Field(..., description="Unique identifier of the voter")
    candidate_name: constr(min_length=3, max_length=50) = Field(..., description="Name of the candidate being voted for")


class VoteCastingResponse(BaseModel):
    vote_id: UUID = Field(..., description="Unique identifier for the cast vote")
    election_id: UUID = Field(..., description="Unique identifier of the election")
    voter_id: UUID = Field(..., description="Unique identifier of the voter")
    candidate_name: str = Field(..., description="Name of the candidate voted for")
    timestamp: datetime = Field(..., description="Timestamp when the vote was cast")


# Election Results Schema
class ElectionResult(BaseModel):
    candidate_name: str = Field(..., description="Name of the candidate")
    vote_count: int = Field(..., ge=0, description="Number of votes received by the candidate")


class ElectionResultsResponse(BaseModel):
    election_id: UUID = Field(..., description="Unique identifier of the election")
    title: str = Field(..., description="Title of the election")
    total_votes: int = Field(..., ge=0, description="Total number of votes cast in the election")
    results: List[ElectionResult] = Field(..., description="List of candidates and their respective vote counts")


# General Error Response Schema
class ErrorResponse(BaseModel):
    error_code: int = Field(..., description="HTTP status code of the error")
    error_message: str = Field(..., description="Detailed error message")
    timestamp: datetime = Field(..., description="Timestamp when the error occurred")


# Example Usage
class ExampleUsage:
    """
    Example usage of the schemas for documentation purposes.
    """

    @staticmethod
    def user_registration_example():
        return UserRegistrationRequest(
            username="john_doe",
            email="john.doe@example.com",
            password="SecureP@ssw0rd",
            is_admin=False
        )

    @staticmethod
    def election_creation_example():
        return ElectionCreationRequest(
            title="Presidential Election 2024",
            description="Election to choose the next president",
            start_time=datetime(2024, 1, 1, 9, 0, 0),
            end_time=datetime(2024, 1, 1, 17, 0, 0),
            candidates=["Alice Johnson", "Bob Smith"]
        )

    @staticmethod
    def vote_casting_example():
        return VoteCastingRequest(
            election_id="123e4567-e89b-12d3-a456-426614174000",
            voter_id="123e4567-e89b-12d3-a456-426614174001",
            candidate_name="Alice Johnson"
        )

    @staticmethod
    def election_results_example():
        return ElectionResultsResponse(
            election_id="123e4567-e89b-12d3-a456-426614174000",
            title="Presidential Election 2024",
            total_votes=1000,
            results=[
                ElectionResult(candidate_name="Alice Johnson", vote_count=600),
                ElectionResult(candidate_name="Bob Smith", vote_count=400)
            ]
        )