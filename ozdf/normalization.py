"""
Text normalization utilities.

This module handles:
- Whitespace collapsing (tabs, multiple spaces -> single space)
- Paragraph detection and preservation
- Text normalization during write operations
"""

import re
import textwrap
from typing import List


def normalize_paragraphs(paragraphs: List[str]) -> List[str]:
    """
    Normalize each paragraph in a list by applying normalize_text to each one.

    Args:
        paragraphs: List of paragraph strings to normalize

    Returns:
        List of normalized paragraph strings
    """
    return [normalize_text(p) for p in paragraphs]


def normalize_text(text: str) -> str:
    """
    Normalize text by collapsing whitespace while preserving paragraph structure.

    Rules:
    - Multiple spaces, tabs, single newlines -> single space
    - Double newlines (blank lines) separate paragraphs
    - Leading/trailing whitespace is trimmed

    Args:
        text: The raw text to normalize

    Returns:
        Normalized text
    """
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def split_into_paragraphs(text: str) -> List[str]:
    """
    Split text into paragraphs based on blank lines (one or more empty lines).

    Args:
        text: The text to split

    Returns:
        List of paragraph strings (stripped, with empty paragraphs removed)
    """
    # Split on blank lines (lines with only whitespace)
    paragraphs = re.split(r'\n\s*\n', text)

    # Strip each paragraph, then filter out empty ones
    stripped_paragraphs = [p.strip() for p in paragraphs]
    return [p for p in stripped_paragraphs if p]


def wrap_to_80_chars(text: str) -> str:
    """
    Wrap text to 80 characters per line, preserving word boundaries.

    Lines are wrapped at spaces to avoid breaking words. If a word is longer
    than 80 characters with no spaces, it will not be broken.

    Args:
        text: The text to wrap (single paragraph)

    Returns:
        The wrapped text with newlines inserted at appropriate positions
    """
    return textwrap.fill(
        text,
        width=80,
        break_long_words=False,
        break_on_hyphens=False
    )
