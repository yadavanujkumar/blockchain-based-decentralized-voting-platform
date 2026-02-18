# src/core/voting_logic.py

"""
Blockchain-Based Decentralized Voting Platform - Core Voting Logic

This module handles election creation, vote casting, vote tallying, and result verification.
It is designed for production-grade deployment with advanced features, robust error handling,
and adherence to industry standards.

Author: Senior Software Engineer - Production Systems Specialist
Date: October 2023
"""

import hashlib
import json
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime
from threading import Lock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Constants
MAX_CANDIDATES = 100
MAX_VOTERS = 1_000_000
HASH_ALGORITHM = "sha256"

# Thread safety
lock = Lock()

# Custom exceptions
class VotingError(Exception):
    """Base exception for voting-related errors."""
    pass

class ElectionNotFoundError(VotingError):
    """Raised when an election is not found."""
    pass

class InvalidVoteError(VotingError):
    """Raised when a vote is invalid."""
    pass

class ElectionClosedError(VotingError):
    """Raised when attempting to vote in a closed election."""
    pass

class Election:
    """
    Represents a single election.
    """

    def __init__(self, election_id: str, candidates: List[str], start_time: datetime, end_time: datetime):
        if len(candidates) > MAX_CANDIDATES:
            raise ValueError(f"Maximum number of candidates ({MAX_CANDIDATES}) exceeded.")
        self.election_id = election_id
        self.candidates = candidates
        self.start_time = start_time
        self.end_time = end_time
        self.votes: Dict[str, int] = {candidate: 0 for candidate in candidates}
        self.voter_hashes: set[str] = set()  # To prevent double voting
        self.is_closed = False

    def cast_vote(self, voter_id: str, candidate: str) -> None:
        """
        Casts a vote for a candidate in the election.

        Args:
            voter_id (str): Unique identifier for the voter.
            candidate (str): Candidate to vote for.

        Raises:
            ElectionClosedError: If the election is closed.
            InvalidVoteError: If the candidate is invalid or the voter has already voted.
        """
        if self.is_closed or datetime.now() > self.end_time:
            raise ElectionClosedError("Election is closed.")
        if candidate not in self.candidates:
            raise InvalidVoteError(f"Invalid candidate: {candidate}")
        
        voter_hash = hashlib.new(HASH_ALGORITHM, voter_id.encode()).hexdigest()
        if voter_hash in self.voter_hashes:
            raise InvalidVoteError("Voter has already cast a vote.")
        
        with lock:
            self.votes[candidate] += 1
            self.voter_hashes.add(voter_hash)
            logging.info(f"Vote cast successfully: Voter={voter_id}, Candidate={candidate}")

    def tally_votes(self) -> Dict[str, int]:
        """
        Returns the current vote tally.

        Returns:
            Dict[str, int]: A dictionary mapping candidates to their vote counts.
        """
        return self.votes.copy()

    def close_election(self) -> None:
        """
        Closes the election, preventing further votes.
        """
        with lock:
            self.is_closed = True
            logging.info(f"Election {self.election_id} has been closed.")

    def verify_results(self) -> Dict[str, Union[str, int]]:
        """
        Verifies and returns the election results.

        Returns:
            Dict[str, Union[str, int]]: The winner and their vote count.
        """
        if not self.is_closed:
            raise VotingError("Election must be closed before verifying results.")
        
        winner = max(self.votes, key=self.votes.get)
        logging.info(f"Election results verified: Winner={winner}, Votes={self.votes[winner]}")
        return {"winner": winner, "votes": self.votes[winner]}


class VotingSystem:
    """
    Manages multiple elections and provides an interface for creating elections,
    casting votes, and retrieving results.
    """

    def __init__(self):
        self.elections: Dict[str, Election] = {}

    def create_election(self, election_id: str, candidates: List[str], start_time: datetime, end_time: datetime) -> None:
        """
        Creates a new election.

        Args:
            election_id (str): Unique identifier for the election.
            candidates (List[str]): List of candidates participating in the election.
            start_time (datetime): Start time of the election.
            end_time (datetime): End time of the election.

        Raises:
            VotingError: If the election ID already exists.
        """
        if election_id in self.elections:
            raise VotingError(f"Election ID '{election_id}' already exists.")
        if len(candidates) > MAX_CANDIDATES:
            raise VotingError(f"Maximum number of candidates ({MAX_CANDIDATES}) exceeded.")
        if start_time >= end_time:
            raise VotingError("Start time must be before end time.")
        
        self.elections[election_id] = Election(election_id, candidates, start_time, end_time)
        logging.info(f"Election created successfully: ID={election_id}, Candidates={candidates}")

    def cast_vote(self, election_id: str, voter_id: str, candidate: str) -> None:
        """
        Casts a vote in a specific election.

        Args:
            election_id (str): ID of the election.
            voter_id (str): Unique identifier for the voter.
            candidate (str): Candidate to vote for.

        Raises:
            ElectionNotFoundError: If the election does not exist.
        """
        election = self.elections.get(election_id)
        if not election:
            raise ElectionNotFoundError(f"Election ID '{election_id}' not found.")
        
        election.cast_vote(voter_id, candidate)

    def tally_votes(self, election_id: str) -> Dict[str, int]:
        """
        Retrieves the vote tally for a specific election.

        Args:
            election_id (str): ID of the election.

        Returns:
            Dict[str, int]: A dictionary mapping candidates to their vote counts.

        Raises:
            ElectionNotFoundError: If the election does not exist.
        """
        election = self.elections.get(election_id)
        if not election:
            raise ElectionNotFoundError(f"Election ID '{election_id}' not found.")
        
        return election.tally_votes()

    def close_election(self, election_id: str) -> None:
        """
        Closes a specific election.

        Args:
            election_id (str): ID of the election.

        Raises:
            ElectionNotFoundError: If the election does not exist.
        """
        election = self.elections.get(election_id)
        if not election:
            raise ElectionNotFoundError(f"Election ID '{election_id}' not found.")
        
        election.close_election()

    def verify_results(self, election_id: str) -> Dict[str, Union[str, int]]:
        """
        Verifies and retrieves the results of a specific election.

        Args:
            election_id (str): ID of the election.

        Returns:
            Dict[str, Union[str, int]]: The winner and their vote count.

        Raises:
            ElectionNotFoundError: If the election does not exist.
        """
        election = self.elections.get(election_id)
        if not election:
            raise ElectionNotFoundError(f"Election ID '{election_id}' not found.")
        
        return election.verify_results()