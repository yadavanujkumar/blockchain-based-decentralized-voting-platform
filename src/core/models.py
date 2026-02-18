# src/core/models.py

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    DateTime,
    Boolean,
    Text,
    UniqueConstraint,
    CheckConstraint,
    Index,
    event,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
    Encoding,
    PublicFormat,
    PrivateFormat,
    NoEncryption,
)

Base = declarative_base()

# Utility functions for cryptographic signing and verification
def sign_data(private_key_pem: bytes, data: str) -> str:
    private_key = load_pem_private_key(private_key_pem, password=None)
    signature = private_key.sign(
        data.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    return signature.hex()

def verify_signature(public_key_pem: bytes, data: str, signature: str) -> bool:
    public_key = load_pem_public_key(public_key_pem)
    try:
        public_key.verify(
            bytes.fromhex(signature),
            data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False

# Base model for audit columns
class AuditMixin:
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    @hybrid_property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

# User model
class User(Base, AuditMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    public_key = Column(Text, nullable=False)  # PEM format public key
    private_key = Column(Text, nullable=False)  # PEM format private key (encrypted)

    votes = relationship("Vote", back_populates="user")

    __table_args__ = (
        UniqueConstraint("username", "email", name="uq_user_username_email"),
        CheckConstraint("LENGTH(username) >= 3", name="check_username_length"),
        Index("idx_user_email", "email"),
    )

# Election model
class Election(Base, AuditMixin):
    __tablename__ = "elections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    votes = relationship("Vote", back_populates="election")

    __table_args__ = (
        CheckConstraint("end_time > start_time", name="check_election_time"),
        Index("idx_election_name", "name"),
    )

# Vote model
class Vote(Base, AuditMixin):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    election_id = Column(Integer, ForeignKey("elections.id", ondelete="CASCADE"), nullable=False)
    vote_data = Column(Text, nullable=False)  # Encrypted vote data
    signature = Column(Text, nullable=False)  # Cryptographic signature of the vote

    user = relationship("User", back_populates="votes")
    election = relationship("Election", back_populates="votes")

    __table_args__ = (
        UniqueConstraint("user_id", "election_id", name="uq_vote_user_election"),
        Index("idx_vote_user_election", "user_id", "election_id"),
    )

    def sign_vote(self, private_key_pem: bytes):
        """Sign the vote data using the user's private key."""
        self.signature = sign_data(private_key_pem, self.vote_data)

    def verify_vote(self, public_key_pem: bytes) -> bool:
        """Verify the vote signature using the user's public key."""
        return verify_signature(public_key_pem, self.vote_data, self.signature)

# Blockchain Transaction model
class BlockchainTransaction(Base, AuditMixin):
    __tablename__ = "blockchain_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_hash = Column(String(64), nullable=False, unique=True)  # SHA-256 hash
    payload = Column(Text, nullable=False)  # Serialized transaction payload
    timestamp = Column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("transaction_hash", name="uq_transaction_hash"),
        Index("idx_transaction_timestamp", "timestamp"),
    )

# Event listeners for soft deletes
@event.listens_for(Base, "before_delete")
def soft_delete(mapper, connection, target):
    if hasattr(target, "deleted_at"):
        target.deleted_at = datetime.utcnow()
        connection.execute(
            target.__table__.update().where(target.__table__.c.id == target.id).values(deleted_at=target.deleted_at)
        )
        raise Exception("Soft delete triggered; no hard delete performed.")