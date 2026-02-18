import pytest
import time
import random
from unittest.mock import MagicMock
from typing import List, Dict

# Constants for test configuration
TRANSACTION_BATCH_SIZES = [10, 100, 1000]
BLOCK_CREATION_TIMES = [1, 2, 5]  # in seconds
NETWORK_NODES = [3, 5, 10]
MAX_SYNC_DELAY = 2  # in seconds
MAX_TRANSACTION_THROUGHPUT = 1000  # transactions per second

# Mocked blockchain and network components
class MockBlockchain:
    def __init__(self, block_creation_time: int):
        self.block_creation_time = block_creation_time
        self.blocks = []
        self.pending_transactions = []

    def add_transaction(self, transaction: Dict):
        self.pending_transactions.append(transaction)

    def create_block(self):
        time.sleep(self.block_creation_time)
        block = {
            "transactions": self.pending_transactions,
            "timestamp": time.time(),
        }
        self.blocks.append(block)
        self.pending_transactions = []
        return block

    def get_block_count(self):
        return len(self.blocks)

class MockNetwork:
    def __init__(self, nodes: int):
        self.nodes = nodes
        self.sync_delay = random.uniform(0.5, MAX_SYNC_DELAY)

    def synchronize(self):
        time.sleep(self.sync_delay)
        return True

# Fixtures
@pytest.fixture
def blockchain():
    """Fixture to initialize a mocked blockchain."""
    return MockBlockchain(block_creation_time=2)

@pytest.fixture
def network():
    """Fixture to initialize a mocked network."""
    return MockNetwork(nodes=5)

@pytest.fixture
def transactions():
    """Fixture to generate a batch of transactions."""
    def _generate_transactions(count: int) -> List[Dict]:
        return [{"id": i, "data": f"Transaction {i}"} for i in range(count)]
    return _generate_transactions

# Tests
def test_block_creation_time(blockchain):
    """
    Test that the blockchain creates blocks within the expected time frame.
    """
    start_time = time.time()
    blockchain.create_block()
    end_time = time.time()
    elapsed_time = end_time - start_time

    assert elapsed_time >= blockchain.block_creation_time, (
        f"Block creation took less time than expected: {elapsed_time}s"
    )
    assert elapsed_time <= blockchain.block_creation_time + 1, (
        f"Block creation exceeded expected time: {elapsed_time}s"
    )

@pytest.mark.parametrize("batch_size", TRANSACTION_BATCH_SIZES)
def test_transaction_throughput(blockchain, transactions, batch_size):
    """
    Test the blockchain's transaction throughput for different batch sizes.
    """
    tx_batch = transactions(batch_size)
    start_time = time.time()
    for tx in tx_batch:
        blockchain.add_transaction(tx)
    blockchain.create_block()
    end_time = time.time()

    throughput = batch_size / (end_time - start_time)
    assert throughput <= MAX_TRANSACTION_THROUGHPUT, (
        f"Transaction throughput exceeded limit: {throughput} tx/s"
    )
    assert len(blockchain.blocks[-1]["transactions"]) == batch_size, (
        f"Block does not contain the expected number of transactions: {len(blockchain.blocks[-1]['transactions'])}"
    )

@pytest.mark.parametrize("nodes", NETWORK_NODES)
def test_network_synchronization_time(network, nodes):
    """
    Test that the network synchronizes within the acceptable delay for different node counts.
    """
    network.nodes = nodes
    start_time = time.time()
    sync_success = network.synchronize()
    end_time = time.time()
    elapsed_time = end_time - start_time

    assert sync_success, "Network synchronization failed."
    assert elapsed_time <= MAX_SYNC_DELAY, (
        f"Network synchronization exceeded maximum delay: {elapsed_time}s"
    )

def test_blockchain_handles_empty_transactions(blockchain):
    """
    Test that the blockchain can handle an empty transaction list gracefully.
    """
    block = blockchain.create_block()
    assert block["transactions"] == [], "Block should contain no transactions."
    assert blockchain.get_block_count() == 1, "Blockchain should have exactly one block."

def test_blockchain_handles_large_transaction_batches(blockchain, transactions):
    """
    Test that the blockchain can handle a large number of transactions in a single block.
    """
    large_batch = transactions(10000)
    for tx in large_batch:
        blockchain.add_transaction(tx)
    block = blockchain.create_block()

    assert len(block["transactions"]) == 10000, (
        f"Block does not contain the expected number of transactions: {len(block['transactions'])}"
    )

def test_network_fails_with_high_latency(monkeypatch, network):
    """
    Test that the network fails to synchronize if latency exceeds the maximum allowed delay.
    """
    def mock_sync_delay():
        time.sleep(MAX_SYNC_DELAY + 1)
        return False

    monkeypatch.setattr(network, "synchronize", mock_sync_delay)
    start_time = time.time()
    sync_success = network.synchronize()
    end_time = time.time()
    elapsed_time = end_time - start_time

    assert not sync_success, "Network synchronization should fail with high latency."
    assert elapsed_time > MAX_SYNC_DELAY, (
        f"Synchronization completed too quickly: {elapsed_time}s"
    )

def test_blockchain_resilience_under_load(blockchain, transactions):
    """
    Test the blockchain's resilience under high load by simulating multiple blocks with transactions.
    """
    for _ in range(10):  # Simulate 10 blocks
        tx_batch = transactions(1000)
        for tx in tx_batch:
            blockchain.add_transaction(tx)
        block = blockchain.create_block()

        assert len(block["transactions"]) == 1000, (
            f"Block does not contain the expected number of transactions: {len(block['transactions'])}"
        )

    assert blockchain.get_block_count() == 10, (
        f"Blockchain should contain 10 blocks, found: {blockchain.get_block_count()}"
    )