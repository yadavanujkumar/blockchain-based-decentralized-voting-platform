# src/pipeline/blockchain_sync.py

"""
Blockchain Synchronization Module for Decentralized Voting Platform.

This module ensures all nodes in the network maintain a consistent view of the blockchain.
It handles:
- Synchronization of the blockchain across nodes.
- Conflict resolution using the longest valid chain rule.
- Chain reorganization in case of discrepancies.

Features:
- Thread-safe and memory-efficient.
- Optimized for performance and scalability.
- Comprehensive error handling and logging.
- Fully type-annotated for type safety.
- Designed with SOLID principles for maintainability and extensibility.

Author: Senior Software Engineer - Production Systems Specialist
"""

from __future__ import annotations
from typing import List, Dict, Optional, Any
import hashlib
import json
import threading
import logging
from time import sleep
from datetime import datetime
import requests

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("BlockchainSync")

class Block:
    """
    Represents a single block in the blockchain.
    """
    def __init__(self, index: int, timestamp: str, data: Dict[str, Any], previous_hash: str, nonce: int = 0):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        """
        Computes the hash of the block using SHA-256.
        """
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def __repr__(self) -> str:
        return f"Block(index={self.index}, hash={self.hash[:10]}...)"


class Blockchain:
    """
    Represents the blockchain and provides methods for synchronization and validation.
    """
    def __init__(self):
        self.chain: List[Block] = []
        self.lock = threading.Lock()
        self.create_genesis_block()

    def create_genesis_block(self) -> None:
        """
        Creates the genesis block and appends it to the chain.
        """
        genesis_block = Block(0, str(datetime.utcnow()), {"message": "Genesis Block"}, "0")
        self.chain.append(genesis_block)
        logger.info("Genesis block created.")

    def add_block(self, block: Block) -> bool:
        """
        Adds a block to the blockchain after validation.
        """
        with self.lock:
            if self.is_valid_block(block, self.chain[-1]):
                self.chain.append(block)
                logger.info(f"Block added to chain: {block}")
                return True
            else:
                logger.warning(f"Invalid block rejected: {block}")
                return False

    def is_valid_block(self, block: Block, previous_block: Block) -> bool:
        """
        Validates a block against the previous block.
        """
        if block.previous_hash != previous_block.hash:
            return False
        if block.index != previous_block.index + 1:
            return False
        if block.hash != block.compute_hash():
            return False
        return True

    def is_valid_chain(self, chain: List[Block]) -> bool:
        """
        Validates the entire blockchain.
        """
        for i in range(1, len(chain)):
            if not self.is_valid_block(chain[i], chain[i - 1]):
                return False
        return True

    def resolve_conflicts(self, neighbor_chains: List[List[Block]]) -> bool:
        """
        Resolves conflicts by adopting the longest valid chain.
        """
        with self.lock:
            longest_chain = self.chain
            for chain in neighbor_chains:
                if len(chain) > len(longest_chain) and self.is_valid_chain(chain):
                    longest_chain = chain
            if longest_chain != self.chain:
                self.chain = longest_chain
                logger.info("Chain replaced with a longer valid chain.")
                return True
            return False


class BlockchainSync:
    """
    Handles synchronization of the blockchain across nodes.
    """
    def __init__(self, blockchain: Blockchain, peers: List[str]):
        self.blockchain = blockchain
        self.peers = peers
        self.sync_interval = 10  # seconds

    def fetch_chain_from_peer(self, peer: str) -> Optional[List[Block]]:
        """
        Fetches the blockchain from a peer node.
        """
        try:
            response = requests.get(f"{peer}/chain")
            if response.status_code == 200:
                chain_data = response.json()
                return [self.deserialize_block(block) for block in chain_data]
            else:
                logger.warning(f"Failed to fetch chain from peer {peer}. HTTP {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Error fetching chain from peer {peer}: {e}")
        return None

    def synchronize(self) -> None:
        """
        Periodically synchronizes the blockchain with peers.
        """
        while True:
            logger.info("Starting blockchain synchronization...")
            neighbor_chains = []
            for peer in self.peers:
                chain = self.fetch_chain_from_peer(peer)
                if chain:
                    neighbor_chains.append(chain)
            if self.blockchain.resolve_conflicts(neighbor_chains):
                logger.info("Blockchain synchronized with the network.")
            else:
                logger.info("No conflicts detected. Blockchain is up-to-date.")
            sleep(self.sync_interval)

    @staticmethod
    def deserialize_block(block_data: Dict[str, Any]) -> Block:
        """
        Deserializes a block from a dictionary.
        """
        return Block(
            index=block_data["index"],
            timestamp=block_data["timestamp"],
            data=block_data["data"],
            previous_hash=block_data["previous_hash"],
            nonce=block_data["nonce"],
        )


if __name__ == "__main__":
    # Example usage
    blockchain = Blockchain()
    peers = ["http://node1.example.com", "http://node2.example.com"]
    sync_service = BlockchainSync(blockchain, peers)

    # Start synchronization in a separate thread
    sync_thread = threading.Thread(target=sync_service.synchronize, daemon=True)
    sync_thread.start()

    # Simulate adding a new block
    new_block = Block(1, str(datetime.utcnow()), {"vote": "Alice -> Bob"}, blockchain.chain[-1].hash)
    blockchain.add_block(new_block)

    # Keep the main thread alive
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down blockchain sync service.")