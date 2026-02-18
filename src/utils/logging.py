# src/utils/logging.py

import logging
import logging.handlers
import json
import os
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """
    Custom logging formatter to output logs in structured JSON format.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "pathname": record.pathname,
            "lineno": record.lineno,
            "funcName": record.funcName,
            "process": record.process,
            "thread": record.thread,
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


class LoggingConfig:
    """
    Configures logging for the application with JSON formatting, log rotation,
    and optional integration with centralized log aggregation systems.
    """

    DEFAULT_LOG_LEVEL = logging.INFO
    LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "logs/app.log")
    LOG_FILE_MAX_BYTES = int(os.getenv("LOG_FILE_MAX_BYTES", 10 * 1024 * 1024))  # 10 MB
    LOG_FILE_BACKUP_COUNT = int(os.getenv("LOG_FILE_BACKUP_COUNT", 5))  # Keep 5 backups
    ENABLE_CONSOLE_LOGGING = os.getenv("ENABLE_CONSOLE_LOGGING", "true").lower() == "true"

    @staticmethod
    def configure_logging() -> None:
        """
        Configures the logging system for the application.
        """
        # Ensure the log directory exists
        log_dir = os.path.dirname(LoggingConfig.LOG_FILE_PATH)
        os.makedirs(log_dir, exist_ok=True)

        # Create the root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(LoggingConfig.DEFAULT_LOG_LEVEL)
        root_logger.handlers.clear()

        # Create a JSON formatter
        json_formatter = JSONFormatter()

        # File handler with log rotation
        file_handler = logging.handlers.RotatingFileHandler(
            LoggingConfig.LOG_FILE_PATH,
            maxBytes=LoggingConfig.LOG_FILE_MAX_BYTES,
            backupCount=LoggingConfig.LOG_FILE_BACKUP_COUNT,
        )
        file_handler.setFormatter(json_formatter)
        root_logger.addHandler(file_handler)

        # Optional console handler
        if LoggingConfig.ENABLE_CONSOLE_LOGGING:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(json_formatter)
            root_logger.addHandler(console_handler)

        # Log the initialization of the logging system
        logging.info("Logging has been configured successfully.")

    @staticmethod
    def set_log_level(level: str) -> None:
        """
        Dynamically sets the log level for the root logger.

        Args:
            level (str): The log level to set (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
        """
        numeric_level = getattr(logging, level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Invalid log level: {level}")
        logging.getLogger().setLevel(numeric_level)
        logging.info(f"Log level set to {level}")


def get_logger(name: str) -> logging.Logger:
    """
    Retrieves a logger instance with the specified name.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: Configured logger instance.
    """
    return logging.getLogger(name)


# Initialize logging configuration on module import
LoggingConfig.configure_logging()