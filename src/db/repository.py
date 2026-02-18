# src/db/repository.py

from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from sqlalchemy import create_engine, exc, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import as_declarative, declared_attr
import logging
import os
from contextlib import contextmanager
from functools import wraps

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type variable for generic repository
T = TypeVar("T", bound="Base")

# Base class for SQLAlchemy models
@as_declarative()
class Base:
    id: Any
    __name__: str

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

# Repository Exception Classes
class RepositoryError(Exception):
    """Base exception for repository errors."""
    pass

class NotFoundError(RepositoryError):
    """Raised when an entity is not found."""
    pass

class DatabaseConnectionError(RepositoryError):
    """Raised when a database connection fails."""
    pass

# Database Configuration
class DatabaseConfig:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
        self.pool_size = int(os.getenv("DB_POOL_SIZE", 5))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", 10))
        self.echo = os.getenv("DB_ECHO", "false").lower() == "true"

    def get_engine(self):
        try:
            return create_engine(
                self.database_url,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                echo=self.echo,
                future=True,
            )
        except exc.SQLAlchemyError as e:
            logger.error(f"Failed to create database engine: {e}")
            raise DatabaseConnectionError("Could not connect to the database.") from e

# Dependency Injection for Session Management
class SessionManager:
    def __init__(self, engine):
        self._session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    @contextmanager
    def session_scope(self) -> Session:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except exc.SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database operation failed: {e}")
            raise RepositoryError("Database operation failed.") from e
        finally:
            session.close()

# Repository Pattern Implementation
class Repository:
    def __init__(self, session_manager: SessionManager, model: Type[T]):
        self._session_manager = session_manager
        self._model = model

    def _handle_exceptions(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exc.SQLAlchemyError as e:
                logger.error(f"Repository operation failed: {e}")
                raise RepositoryError("Repository operation failed.") from e
        return wrapper

    @_handle_exceptions
    def get_by_id(self, entity_id: Any) -> Optional[T]:
        with self._session_manager.session_scope() as session:
            entity = session.get(self._model, entity_id)
            if not entity:
                raise NotFoundError(f"Entity with ID {entity_id} not found.")
            return entity

    @_handle_exceptions
    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        with self._session_manager.session_scope() as session:
            query = session.query(self._model)
            if filters:
                query = query.filter_by(**filters)
            return query.all()

    @_handle_exceptions
    def create(self, entity_data: Dict[str, Any]) -> T:
        with self._session_manager.session_scope() as session:
            entity = self._model(**entity_data)
            session.add(entity)
            session.flush()  # Ensure the ID is populated
            return entity

    @_handle_exceptions
    def update(self, entity_id: Any, update_data: Dict[str, Any]) -> T:
        with self._session_manager.session_scope() as session:
            entity = session.get(self._model, entity_id)
            if not entity:
                raise NotFoundError(f"Entity with ID {entity_id} not found.")
            for key, value in update_data.items():
                setattr(entity, key, value)
            session.flush()
            return entity

    @_handle_exceptions
    def delete(self, entity_id: Any) -> None:
        with self._session_manager.session_scope() as session:
            entity = session.get(self._model, entity_id)
            if not entity:
                raise NotFoundError(f"Entity with ID {entity_id} not found.")
            session.delete(entity)

# Example Usage
if __name__ == "__main__":
    # Example model
    class User(Base):
        __tablename__ = "users"
        id: int
        name: str
        email: str

    # Initialize database components
    config = DatabaseConfig()
    engine = config.get_engine()
    session_manager = SessionManager(engine)

    # Create tables (for demonstration purposes)
    Base.metadata.create_all(engine)

    # Use the repository
    user_repository = Repository(session_manager, User)

    # Example operations
    try:
        # Create a new user
        new_user = user_repository.create({"name": "Alice", "email": "alice@example.com"})
        logger.info(f"Created user: {new_user}")

        # Fetch user by ID
        fetched_user = user_repository.get_by_id(new_user.id)
        logger.info(f"Fetched user: {fetched_user}")

        # Update user
        updated_user = user_repository.update(new_user.id, {"name": "Alice Updated"})
        logger.info(f"Updated user: {updated_user}")

        # Delete user
        user_repository.delete(updated_user.id)
        logger.info("User deleted successfully.")

    except RepositoryError as e:
        logger.error(f"An error occurred: {e}")