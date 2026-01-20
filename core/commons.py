# core/commons.py
"""Shared configuration and utility functions."""
import json
import re
from pathlib import Path
from typing import Optional
import yaml


class InvalidResearchIdError(ValueError):
    """Raised when a research ID contains invalid characters."""
    pass


def validate_research_id(research_id: str) -> str:
    """Validate research_id to prevent path traversal attacks.

    Args:
        research_id: Research ID to validate

    Returns:
        The validated research_id

    Raises:
        InvalidResearchIdError: If research_id contains invalid characters
    """
    if not research_id:
        raise InvalidResearchIdError("Research ID cannot be empty")
    if not re.match(r'^[a-zA-Z0-9_-]+$', research_id):
        raise InvalidResearchIdError(
            f"Invalid research ID: '{research_id}'. "
            "Only alphanumeric characters, underscores, and hyphens are allowed."
        )
    return research_id


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config file (default: config.yaml)

    Returns:
        Configuration dictionary, or empty dict if file not found
    """
    config_file = Path(config_path)
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}


def get_path(config: dict, key: str, default: str) -> Path:
    """Get a path from config with fallback default.

    Args:
        config: Configuration dictionary
        key: Key name under 'paths' section
        default: Default path if not found

    Returns:
        Path object
    """
    if config and "paths" in config and key in config["paths"]:
        return Path(config["paths"][key])
    return Path(default)


def get_research_history_path(config: dict) -> Path:
    """Get research history path from config."""
    return get_path(config, "research_history", "./research_history")


def get_rag_db_path(config: dict) -> Path:
    """Get RAG database path from config."""
    return get_path(config, "rag_db", "./chroma_db")


def load_research(research_id: str, research_history_path: Path, raise_if_missing: bool = True) -> Optional[dict]:
    """Load research data from JSON file.

    Args:
        research_id: Research ID
        research_history_path: Path to research history directory
        raise_if_missing: If True, raise FileNotFoundError when not found.
                          If False, return None when not found.

    Returns:
        Research data dictionary, or None if not found and raise_if_missing=False

    Raises:
        FileNotFoundError: If research file does not exist and raise_if_missing=True
        InvalidResearchIdError: If research_id contains invalid characters
    """
    validate_research_id(research_id)
    filepath = research_history_path / f"{research_id}.json"
    if not filepath.exists():
        if raise_if_missing:
            raise FileNotFoundError(f"Research not found: {research_id}")
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_research(research_id: str, data: dict, research_history_path: Path) -> None:
    """Save research data to JSON file.

    Args:
        research_id: Research ID
        data: Research data dictionary
        research_history_path: Path to research history directory

    Raises:
        InvalidResearchIdError: If research_id contains invalid characters
    """
    validate_research_id(research_id)
    research_history_path.mkdir(exist_ok=True)
    filepath = research_history_path / f"{research_id}.json"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
