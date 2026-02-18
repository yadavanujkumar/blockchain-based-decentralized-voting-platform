import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, Any
from voting_logic import cast_vote, validate_vote, tally_votes, VotingError

# Constants for test data
VALID_VOTER_ID = "voter123"
INVALID_VOTER_ID = "invalid_voter"
VALID_CANDIDATE_ID = "candidate456"
INVALID_CANDIDATE_ID = "invalid_candidate"
VALID_VOTE_PAYLOAD = {"voter_id": VALID_VOTER_ID, "candidate_id": VALID_CANDIDATE_ID}
INVALID_VOTE_PAYLOAD = {"voter_id": INVALID_VOTER_ID, "candidate_id": INVALID_CANDIDATE_ID}

@pytest.fixture
def mock_voting_database():
    """
    Fixture to mock the voting database interactions.
    """
    with patch("voting_logic.VotingDatabase") as MockDatabase:
        mock_db = MockDatabase.return_value
        mock_db.is_voter_eligible.return_value = True
        mock_db.is_candidate_valid.return_value = True
        mock_db.record_vote.return_value = True
        yield mock_db

@pytest.fixture
def mock_voting_database_with_errors():
    """
    Fixture to mock the voting database with error scenarios.
    """
    with patch("voting_logic.VotingDatabase") as MockDatabase:
        mock_db = MockDatabase.return_value
        mock_db.is_voter_eligible.side_effect = lambda voter_id: voter_id == VALID_VOTER_ID
        mock_db.is_candidate_valid.side_effect = lambda candidate_id: candidate_id == VALID_CANDIDATE_ID
        mock_db.record_vote.side_effect = VotingError("Database error")
        yield mock_db

def test_cast_vote_happy_path(mock_voting_database):
    """
    Test the happy path for casting a vote.
    """
    result = cast_vote(VALID_VOTE_PAYLOAD)
    assert result is True, "Expected cast_vote to return True for valid input"

def test_cast_vote_invalid_voter(mock_voting_database_with_errors):
    """
    Test casting a vote with an invalid voter ID.
    """
    with pytest.raises(VotingError, match="Voter is not eligible"):
        cast_vote({"voter_id": INVALID_VOTER_ID, "candidate_id": VALID_CANDIDATE_ID})

def test_cast_vote_invalid_candidate(mock_voting_database_with_errors):
    """
    Test casting a vote with an invalid candidate ID.
    """
    with pytest.raises(VotingError, match="Candidate is not valid"):
        cast_vote({"voter_id": VALID_VOTER_ID, "candidate_id": INVALID_CANDIDATE_ID})

def test_cast_vote_database_error(mock_voting_database_with_errors):
    """
    Test casting a vote when the database throws an error.
    """
    with pytest.raises(VotingError, match="Database error"):
        cast_vote(VALID_VOTE_PAYLOAD)

@pytest.mark.parametrize(
    "payload,expected_error",
    [
        ({"voter_id": "", "candidate_id": VALID_CANDIDATE_ID}, "Voter ID cannot be empty"),
        ({"voter_id": VALID_VOTER_ID, "candidate_id": ""}, "Candidate ID cannot be empty"),
        ({"voter_id": None, "candidate_id": VALID_CANDIDATE_ID}, "Voter ID cannot be None"),
        ({"voter_id": VALID_VOTER_ID, "candidate_id": None}, "Candidate ID cannot be None"),
    ],
)
def test_validate_vote_invalid_inputs(payload: Dict[str, Any], expected_error: str):
    """
    Test validation logic for invalid vote inputs.
    """
    with pytest.raises(ValueError, match=expected_error):
        validate_vote(payload)

def test_tally_votes_happy_path(mock_voting_database):
    """
    Test tallying votes in a happy path scenario.
    """
    mock_voting_database.get_all_votes.return_value = [
        {"candidate_id": VALID_CANDIDATE_ID, "count": 10},
        {"candidate_id": "candidate789", "count": 5},
    ]
    result = tally_votes()
    assert result == {"candidate456": 10, "candidate789": 5}, "Tally votes result is incorrect"

def test_tally_votes_empty_database(mock_voting_database):
    """
    Test tallying votes when there are no votes in the database.
    """
    mock_voting_database.get_all_votes.return_value = []
    result = tally_votes()
    assert result == {}, "Expected empty dictionary when no votes are present"

def test_tally_votes_database_error(mock_voting_database_with_errors):
    """
    Test tallying votes when the database throws an error.
    """
    mock_voting_database_with_errors.get_all_votes.side_effect = VotingError("Database error")
    with pytest.raises(VotingError, match="Database error"):
        tally_votes()

@pytest.mark.parametrize(
    "voter_id,candidate_id,expected_result",
    [
        (VALID_VOTER_ID, VALID_CANDIDATE_ID, True),
        (INVALID_VOTER_ID, VALID_CANDIDATE_ID, False),
        (VALID_VOTER_ID, INVALID_CANDIDATE_ID, False),
        (INVALID_VOTER_ID, INVALID_CANDIDATE_ID, False),
    ],
)
def test_cast_vote_parametrized(voter_id: str, candidate_id: str, expected_result: bool, mock_voting_database_with_errors):
    """
    Parametrized test for casting votes with various voter and candidate IDs.
    """
    payload = {"voter_id": voter_id, "candidate_id": candidate_id}
    if expected_result:
        result = cast_vote(payload)
        assert result is True, f"Expected cast_vote to return True for payload: {payload}"
    else:
        with pytest.raises(VotingError):
            cast_vote(payload)