import logging
import os
from typing import Any


def setup_logging() -> logging.Logger:
    """Set up and return a logger instance."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(__name__)


def load_env_var(var_name: str) -> str:
    """
    Load an environment variable or raise an error if it's not set.

    Args:
        var_name (str): Name of the environment variable to load.

    Returns:
        str: Value of the environment variable.

    Raises:
        ValueError: If the environment variable is not set.
    """
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"Environment variable {var_name} is not set.")
    return value


def safe_get(data: dict, key: str, default: Any = None) -> Any:
    """Safely get a value from a dictionary."""
    return data.get(key, default)
