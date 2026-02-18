# src/db/models.py

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
    func,
    Index,
    JSON
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime

Base = declarative_base()

# Utility mixin for audit columns
class AuditMixin:
    @declared_attr
    def created_at(cls):
        return Column(DateTime, nullable=False, default=func.now(), index=True)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), index=True)

    @declared_attr
    def deleted_at(cls):
        return Column(DateTime, nullable=True, index=True)  # Soft delete

    @declared_attr
    def is_deleted(cls):
        return Column(Boolean, nullable=False, default=False, index=True)

# Users table
class User(Base, AuditMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    email = Column(String(100), nullable=False, unique=True, index=True)
    password_hash = Column(String(128), nullable=False)
    is_admin = Column(Boolean, nullable=False, default=False)

    # Relationships
    votes = relationship('Vote', back_populates='user', lazy='selectin')
    elections = relationship('Election', back_populates='creator', lazy='selectin')

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"

# Elections table
class Election(Base, AuditMixin):
    __tablename__ = 'elections'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    creator_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Relationships
    creator = relationship('User', back_populates='elections', lazy='joined')
    votes = relationship('Vote', back_populates='election', lazy='selectin')

    # Constraints
    __table_args__ = (
        CheckConstraint('start_time < end_time', name='check_election_time_validity'),
    )

    def __repr__(self):
        return f"<Election(id={self.id}, title={self.title}, start_time={self.start_time}, end_time={self.end_time})>"

# Votes table
class Vote(Base, AuditMixin):
    __tablename__ = 'votes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    election_id = Column(Integer, ForeignKey('elections.id', ondelete='CASCADE'), nullable=False)
    candidate = Column(String(100), nullable=False)

    # Relationships
    user = relationship('User', back_populates='votes', lazy='joined')
    election = relationship('Election', back_populates='votes', lazy='joined')

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'election_id', name='unique_user_vote_per_election'),
    )

    def __repr__(self):
        return f"<Vote(id={self.id}, user_id={self.user_id}, election_id={self.election_id}, candidate={self.candidate})>"

# Blockchain table
class Blockchain(Base, AuditMixin):
    __tablename__ = 'blockchain'

    id = Column(Integer, primary_key=True, autoincrement=True)
    block_hash = Column(String(64), nullable=False, unique=True, index=True)
    previous_hash = Column(String(64), nullable=False, index=True)
    data = Column(JSON, nullable=False)  # Stores vote data or other relevant information
    timestamp = Column(DateTime, nullable=False, default=func.now())

    # Constraints
    __table_args__ = (
        UniqueConstraint('block_hash', name='unique_block_hash'),
    )

    def __repr__(self):
        return f"<Blockchain(id={self.id}, block_hash={self.block_hash}, previous_hash={self.previous_hash})>"

# Indexing strategy
Index('ix_votes_election_id_candidate', Vote.election_id, Vote.candidate)
Index('ix_blockchain_previous_hash', Blockchain.previous_hash)

# Example of a soft delete filter
def with_soft_delete(query):
    return query.filter_by(is_deleted=False)