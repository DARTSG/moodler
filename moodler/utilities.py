from pathlib import Path


def safe_path(name: str) -> Path:
    """Sanitizes file names to avoid path manipulations"""
    return Path(name.replace("/", "."))