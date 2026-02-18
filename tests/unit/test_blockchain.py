import pytest
from unittest.mock import MagicMock, patch
from blockchain import Blockchain, Block, Transaction, InvalidTransactionError, ConsensusError
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from typing import List

# Constants for test data
TEST_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
TEST_PUBLIC_KEY = TEST_PRIVATE_KEY.public_key()
TEST_SIGNATURE_PADDING = padding.PSS(
    mgf=padding.MGF1(hashes.SHA256()),
    salt_length=padding.PSS.MAX_LENGTH
)
TEST_HASH_ALGORITHM = hashes.SHA256()
TEST_TRANSACTION_DATA = {"voter_id": "12345", "vote": "candidate_a"}
TEST_INVALID_TRANSACTION_DATA = {"voter_id": "", "vote": "candidate_a"}
TEST_BLOCK_DATA = [{"voter_id": "12345", "vote": "candidate_a"}]
TEST_DIFFICULTY = 4

# Helper function to sign data
def sign_data(private_key, data: dict) -> bytes:
    return private_key.sign(
        str(data).encode(),
        TEST_SIGNATURE_PADDING,
        TEST_HASH_ALGORITHM
    )

@pytest.fixture
def blockchain() -> Blockchain:
    """Fixture to create a new blockchain instance."""
    return Blockchain(difficulty=TEST_DIFFICULTY)

@pytest.fixture
def valid_transaction() -> Transaction:
    """Fixture to create a valid transaction."""
    signature = sign_data(TEST_PRIVATE_KEY, TEST_TRANSACTION_DATA)
    return Transaction(
        data=TEST_TRANSACTION_DATA,
        public_key=TEST_PUBLIC_KEY,
        signature=signature
    )

@pytest.fixture
def invalid_transaction() -> Transaction:
    """Fixture to create an invalid transaction."""
    signature = sign_data(TEST_PRIVATE_KEY, TEST_INVALID_TRANSACTION_DATA)
    return Transaction(
        data=TEST_INVALID_TRANSACTION_DATA,
        public_key=TEST_PUBLIC_KEY,
        signature=signature
    )

@pytest.fixture
def valid_block(valid_transaction: Transaction) -> Block:
    """Fixture to create a valid block."""
    return Block(transactions=[valid_transaction], previous_hash="0" * 64)

@pytest.fixture
def invalid_block(invalid_transaction: Transaction) -> Block:
    """Fixture to create an invalid block."""
    return Block(transactions=[invalid_transaction], previous_hash="0" * 64)

def test_block_creation(valid_block: Block):
    """Test block creation with valid data."""
    assert valid_block.transactions, "Block should contain transactions"
    assert valid_block.previous_hash == "0" * 64, "Previous hash should match the genesis block hash"
    assert valid_block.hash, "Block hash should be computed"

def test_transaction_validation(valid_transaction: Transaction):
    """Test transaction validation with valid data."""
    assert valid_transaction.is_valid(), "Transaction should be valid with correct signature and data"

def test_transaction_invalid_signature(invalid_transaction: Transaction):
    """Test transaction validation with invalid signature."""
    invalid_transaction.signature = b"tampered_signature"
    assert not invalid_transaction.is_valid(), "Transaction should be invalid with tampered signature"

def test_transaction_invalid_data(invalid_transaction: Transaction):
    """Test transaction validation with invalid data."""
    assert not invalid_transaction.is_valid(), "Transaction should be invalid with incorrect data"

def test_block_validation(valid_block: Block):
    """Test block validation with valid transactions."""
    assert valid_block.is_valid(), "Block should be valid with correct transactions and hash"

def test_block_invalid_transactions(invalid_block: Block):
    """Test block validation with invalid transactions."""
    assert not invalid_block.is_valid(), "Block should be invalid if it contains invalid transactions"

def test_blockchain_add_block(blockchain: Blockchain, valid_block: Block):
    """Test adding a valid block to the blockchain."""
    blockchain.add_block(valid_block)
    assert len(blockchain.chain) == 2, "Blockchain should contain the genesis block and the new block"
    assert blockchain.chain[-1] == valid_block, "The last block in the chain should be the newly added block"

def test_blockchain_consensus(blockchain: Blockchain):
    """Test blockchain consensus algorithm."""
    other_chain = Blockchain(difficulty=TEST_DIFFICULTY)
    other_chain.add_block(Block(transactions=[], previous_hash=blockchain.chain[-1].hash))
    blockchain.resolve_conflicts([other_chain])
    assert blockchain.chain == other_chain.chain, "Blockchain should adopt the longer valid chain"

def test_blockchain_invalid_consensus(blockchain: Blockchain):
    """Test blockchain consensus with an invalid chain."""
    invalid_chain = Blockchain(difficulty=TEST_DIFFICULTY)
    invalid_chain.chain.append(Block(transactions=[], previous_hash="tampered_hash"))
    with pytest.raises(ConsensusError, match="Invalid chain provided"):
        blockchain.resolve_conflicts([invalid_chain])

@pytest.mark.parametrize("difficulty,expected", [
    (1, True),
    (4, True),
    (5, False),
])
def test_blockchain_proof_of_work(difficulty, expected):
    """Test proof-of-work with varying difficulty levels."""
    blockchain = Blockchain(difficulty=difficulty)
    block = Block(transactions=[], previous_hash="0" * 64)
    blockchain.mine_block(block)
    assert block.hash.startswith("0" * difficulty) == expected, f"Block hash should start with {difficulty} zeros"

def test_blockchain_invalid_block_addition(blockchain: Blockchain, invalid_block: Block):
    """Test adding an invalid block to the blockchain."""
    with pytest.raises(ValueError, match="Invalid block"):
        blockchain.add_block(invalid_block)

def test_blockchain_genesis_block(blockchain: Blockchain):
    """Test the genesis block creation."""
    genesis_block = blockchain.chain[0]
    assert genesis_block.previous_hash == "0" * 64, "Genesis block should have a previous hash of all zeros"
    assert genesis_block.is_valid(), "Genesis block should be valid"