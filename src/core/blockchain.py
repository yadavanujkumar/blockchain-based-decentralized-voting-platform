# src/core/blockchain.py

import hashlib
import time
from typing import List, Optional, Dict, Any
import json
import logging
from threading import Lock

# Configure logging for the blockchain system
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Blockchain")

class Block:
    """
    Represents a single block in the blockchain.
    """

    def __init__(self, index: int, timestamp: float, transactions: List[Dict[str, Any]], previous_hash: str, nonce: int = 0):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        """
        Computes the cryptographic hash of the block's contents.
        """
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def __repr__(self) -> str:
        return f"Block(index={self.index}, hash={self.hash}, previous_hash={self.previous_hash})"


class Blockchain:
    """
    Represents the blockchain and its operations.
    """

    def __init__(self, difficulty: int = 4):
        self.chain: List[Block] = []
        self.unconfirmed_transactions: List[Dict[str, Any]] = []
        self.difficulty = difficulty
        self.lock = Lock()  # Ensures thread safety
        self.create_genesis_block()

    def create_genesis_block(self) -> None:
        """
        Creates the genesis block and appends it to the chain.
        """
        logger.info("Creating genesis block...")
        genesis_block = Block(index=0, timestamp=time.time(), transactions=[], previous_hash="0")
        self.chain.append(genesis_block)
        logger.info(f"Genesis block created: {genesis_block}")

    def add_transaction(self, transaction: Dict[str, Any]) -> None:
        """
        Adds a new transaction to the list of unconfirmed transactions.
        """
        logger.debug(f"Adding transaction: {transaction}")
        self.unconfirmed_transactions.append(transaction)

    def mine(self) -> Optional[Block]:
        """
        Mines a new block by solving the proof-of-work puzzle.
        """
        if not self.unconfirmed_transactions:
            logger.warning("No transactions to mine.")
            return None

        with self.lock:
            logger.info("Mining a new block...")
            last_block = self.chain[-1]
            new_block = Block(
                index=last_block.index + 1,
                timestamp=time.time(),
                transactions=self.unconfirmed_transactions,
                previous_hash=last_block.hash,
            )
            self.proof_of_work(new_block)
            self.chain.append(new_block)
            self.unconfirmed_transactions = []
            logger.info(f"Block mined and added to the chain: {new_block}")
            return new_block

    def proof_of_work(self, block: Block) -> None:
        """
        Implements the proof-of-work algorithm to find a valid nonce for the block.
        """
        logger.debug("Starting proof-of-work...")
        while not block.hash.startswith("0" * self.difficulty):
            block.nonce += 1
            block.hash = block.compute_hash()
        logger.debug(f"Proof-of-work completed: {block.hash}")

    def is_valid_chain(self) -> bool:
        """
        Validates the entire blockchain to ensure integrity.
        """
        logger.info("Validating blockchain integrity...")
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # Validate hash
            if current.hash != current.compute_hash():
                logger.error(f"Invalid hash at block {current.index}")
                return False

            # Validate previous hash
            if current.previous_hash != previous.hash:
                logger.error(f"Invalid previous hash at block {current.index}")
                return False

        logger.info("Blockchain integrity validated successfully.")
        return True

    def get_last_block(self) -> Block:
        """
        Returns the last block in the chain.
        """
        return self.chain[-1]

    def to_dict(self) -> List[Dict[str, Any]]:
        """
        Returns the blockchain as a list of dictionaries.
        """
        return [block.__dict__ for block in self.chain]

    def from_dict(self, chain_data: List[Dict[str, Any]]) -> None:
        """
        Reconstructs the blockchain from a list of dictionaries.
        """
        logger.info("Reconstructing blockchain from data...")
        self.chain = [Block(**block_data) for block_data in chain_data]
        logger.info("Blockchain reconstruction complete.")

    def resolve_conflicts(self, other_chains: List[List[Dict[str, Any]]]) -> bool:
        """
        Resolves conflicts by replacing the chain with the longest valid chain.
        """
        logger.info("Resolving conflicts with other chains...")
        longest_chain = None
        max_length = len(self.chain)

        for chain_data in other_chains:
            chain = [Block(**block_data) for block_data in chain_data]
            if len(chain) > max_length and self.is_valid_chain():
                max_length = len(chain)
                longest_chain = chain

        if longest_chain:
            self.chain = longest_chain
            logger.info("Chain replaced with the longest valid chain.")
            return True

        logger.info("No conflicts found or chain not replaced.")
        return False