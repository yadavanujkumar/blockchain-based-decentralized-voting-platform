import pytest
import requests
from typing import Generator
from requests.models import Response

# Constants
BASE_URL = "http://localhost:8000/api/v1"
USER_REGISTRATION_ENDPOINT = f"{BASE_URL}/users/register"
ELECTION_CREATION_ENDPOINT = f"{BASE_URL}/elections/create"
VOTE_CASTING_ENDPOINT = f"{BASE_URL}/votes/cast"
RESULT_RETRIEVAL_ENDPOINT = f"{BASE_URL}/elections/results"

# Fixtures
@pytest.fixture(scope="module")
def test_user() -> dict:
    """Fixture for test user data."""
    return {
        "username": "test_user",
        "password": "secure_password123",
        "email": "test_user@example.com"
    }

@pytest.fixture(scope="module")
def test_election() -> dict:
    """Fixture for test election data."""
    return {
        "title": "Test Election",
        "description": "This is a test election.",
        "candidates": ["Alice", "Bob", "Charlie"]
    }

@pytest.fixture(scope="module")
def registered_user(test_user: dict) -> Generator[dict, None, None]:
    """Fixture to register a user and provide the user data."""
    response = requests.post(USER_REGISTRATION_ENDPOINT, json=test_user)
    assert response.status_code == 201, f"User registration failed: {response.json()}"
    yield test_user
    # Teardown: Delete the user after tests
    requests.delete(f"{BASE_URL}/users/{test_user['username']}")

@pytest.fixture(scope="module")
def created_election(registered_user: dict, test_election: dict) -> Generator[dict, None, None]:
    """Fixture to create an election and provide the election data."""
    response = requests.post(ELECTION_CREATION_ENDPOINT, json=test_election, auth=(registered_user['username'], registered_user['password']))
    assert response.status_code == 201, f"Election creation failed: {response.json()}"
    election_data = response.json()
    yield election_data
    # Teardown: Delete the election after tests
    requests.delete(f"{ELECTION_CREATION_ENDPOINT}/{election_data['id']}", auth=(registered_user['username'], registered_user['password']))

# Test Cases
def test_user_registration(test_user: dict):
    """Test user registration with valid data."""
    response = requests.post(USER_REGISTRATION_ENDPOINT, json=test_user)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.json()}"
    assert "id" in response.json(), "User ID not returned in response"
    assert response.json()["username"] == test_user["username"], "Username mismatch in response"

@pytest.mark.parametrize("invalid_data", [
    {"username": "", "password": "password123", "email": "user@example.com"},  # Empty username
    {"username": "user", "password": "", "email": "user@example.com"},        # Empty password
    {"username": "user", "password": "password123", "email": ""},             # Empty email
    {"username": "user", "password": "short", "email": "user@example.com"},   # Weak password
])
def test_user_registration_invalid_data(invalid_data: dict):
    """Test user registration with invalid data."""
    response = requests.post(USER_REGISTRATION_ENDPOINT, json=invalid_data)
    assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.json()}"
    assert "error" in response.json(), "Error message not returned in response"

def test_election_creation(registered_user: dict, test_election: dict):
    """Test election creation with valid data."""
    response = requests.post(ELECTION_CREATION_ENDPOINT, json=test_election, auth=(registered_user['username'], registered_user['password']))
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.json()}"
    assert "id" in response.json(), "Election ID not returned in response"
    assert response.json()["title"] == test_election["title"], "Election title mismatch in response"

@pytest.mark.parametrize("invalid_data", [
    {"title": "", "description": "Test description", "candidates": ["Alice", "Bob"]},  # Empty title
    {"title": "Test Election", "description": "", "candidates": ["Alice", "Bob"]},    # Empty description
    {"title": "Test Election", "description": "Test description", "candidates": []},  # No candidates
])
def test_election_creation_invalid_data(registered_user: dict, invalid_data: dict):
    """Test election creation with invalid data."""
    response = requests.post(ELECTION_CREATION_ENDPOINT, json=invalid_data, auth=(registered_user['username'], registered_user['password']))
    assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.json()}"
    assert "error" in response.json(), "Error message not returned in response"

def test_vote_casting(registered_user: dict, created_election: dict):
    """Test vote casting with valid data."""
    vote_data = {"election_id": created_election["id"], "candidate": "Alice"}
    response = requests.post(VOTE_CASTING_ENDPOINT, json=vote_data, auth=(registered_user['username'], registered_user['password']))
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
    assert response.json()["message"] == "Vote successfully cast", "Unexpected response message"

def test_vote_casting_invalid_candidate(registered_user: dict, created_election: dict):
    """Test vote casting with an invalid candidate."""
    vote_data = {"election_id": created_election["id"], "candidate": "InvalidCandidate"}
    response = requests.post(VOTE_CASTING_ENDPOINT, json=vote_data, auth=(registered_user['username'], registered_user['password']))
    assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.json()}"
    assert "error" in response.json(), "Error message not returned in response"

def test_result_retrieval(created_election: dict):
    """Test retrieving election results."""
    response = requests.get(f"{RESULT_RETRIEVAL_ENDPOINT}/{created_election['id']}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
    assert "results" in response.json(), "Results not returned in response"
    assert isinstance(response.json()["results"], dict), "Results should be a dictionary"