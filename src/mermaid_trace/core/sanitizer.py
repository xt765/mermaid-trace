"""
Data Sanitization Module
========================

This module provides functionality to mask sensitive data in trace events.
It ensures that passwords, tokens, and other secrets are not leaked into
logs or diagrams.
"""

from typing import Any
from .config import config


class DataMasker:
    """
    Recursively traverses data structures and masks sensitive values
    based on configured patterns.
    """

    def __init__(self) -> None:
        self.mask_value = config.mask_value
        # Pre-compile regex patterns for performance if they look like regex
        # For simplicity, we'll do simple string matching for keys first,
        # but support regex if the pattern contains special chars.
        self.patterns = config.mask_patterns

    def _is_sensitive(self, key: str) -> bool:
        """Checks if a key matches any of the sensitive patterns."""
        key_lower = key.lower()
        for pattern in self.patterns:
            if pattern.lower() in key_lower:
                return True
        return False

    def mask(self, data: Any, depth: int = 0) -> Any:
        """
        Masks sensitive data in the given object.

        Args:
            data: The data to sanitize.
            depth: Current recursion depth.

        Returns:
            Sanitized data.
        """
        # Stop recursion if too deep
        if depth > config.max_arg_depth:
            return data

        if isinstance(data, dict):
            return {
                k: (
                    self.mask_value
                    if isinstance(k, str) and self._is_sensitive(k)
                    else self.mask(v, depth + 1)
                )
                for k, v in data.items()
            }

        elif isinstance(data, (list, tuple, set)):
            # Handle list/tuple/set by reconstructing them
            # Note: set elements must be hashable, so if we mask them they might collide
            # but usually we mask values in dicts.
            masked_items = [self.mask(item, depth + 1) for item in data]
            if isinstance(data, tuple):
                return tuple(masked_items)
            elif isinstance(data, set):
                return set(masked_items)
            return masked_items

        elif hasattr(data, "__dict__"):
            # For objects, we can't easily modify them in place without side effects.
            # We also don't want to return a dict if the original was an object.
            # But for tracing purposes, we usually convert to string later.
            # If we return the object as is, the sensitive fields are still there.
            #
            # Strategy: We don't mask the object itself, but if this is called
            # before stringification, we might want to return a dict representation
            # with masked values.
            #
            # However, decorators.py typically calls str(args) or repr(args).
            # If we mask here, we should probably return a safe dict representation.
            try:
                safe_dict = {
                    k: (
                        self.mask_value
                        if self._is_sensitive(k)
                        else self.mask(v, depth + 1)
                    )
                    for k, v in data.__dict__.items()
                    if not k.startswith("_")  # Skip private by default?
                }
                return safe_dict
            except Exception:
                # If __dict__ is not accessible or other errors
                return data

        return data


# Global instance
data_masker = DataMasker()
