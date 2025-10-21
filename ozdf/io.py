"""
File I/O and loaders for OZDF.

This module provides the main entry points:
- open_corpus_readonly: Load corpus without save capability
- open_corpus_readwrite: Load and copy corpus with save capability
- open_document: Single document access (no save capability)
"""

from typing import Optional
from ozdf.models import Corpus, Document
from ozdf.parser import parse_document
import os


def _open_corpus(corpus_path: Optional[str], save_path: Optional[str]) -> Corpus:
    """
    Internal function to open a corpus.

    Args:
        corpus_path: Path to the corpus directory to load (None for blank corpus)
        save_path: Path for saving (None for read-only)

    Returns:
        A Corpus object
    """
    # Create corpus with save_path
    corpus = Corpus(save_path=save_path)

    # If corpus_path is provided, load documents
    if corpus_path is not None:
        # Validate corpus_path exists and is a directory
        if not os.path.exists(corpus_path):
            raise FileNotFoundError(f"Corpus path does not exist: {corpus_path}")
        if not os.path.isdir(corpus_path):
            raise NotADirectoryError(f"Corpus path is not a directory: {corpus_path}")

        # Find all .ozdf files and directory documents directly in corpus_path
        document_paths = []
        for item in os.listdir(corpus_path):
            item_path = os.path.join(corpus_path, item)
            # Check if it's a .ozdf file
            if item.endswith('.ozdf') and os.path.isfile(item_path):
                document_paths.append(item_path)
            # Check if it's a directory document (contains _metadata.ozdf or .ozdf_writing)
            elif os.path.isdir(item_path):
                has_metadata = os.path.exists(os.path.join(item_path, '_metadata.ozdf'))
                has_writing_marker = os.path.exists(os.path.join(item_path, '.ozdf_writing'))
                if has_metadata or has_writing_marker:
                    document_paths.append(item_path)

        # Sort for consistent ordering
        document_paths.sort()

        # Parse and add each document to corpus
        for file_path in document_paths:
            document = parse_document(file_path)
            corpus._add_existing_document(document)

    # If save_path is provided, create directory and save all documents
    if save_path is not None:
        # Validate save_path doesn't exist
        if os.path.exists(save_path):
            raise FileExistsError(f"Output path already exists: {save_path}")

        # Create save_path directory
        os.makedirs(save_path)

        corpus.save()

    return corpus


def open_corpus_readonly(corpus_path: str) -> Corpus:
    """
    Open a corpus without save capability.

    The entire corpus is loaded into memory immediately.
    Calling save() on this corpus will raise an exception.

    Args:
        corpus_path: Path to the corpus directory

    Returns:
        A Corpus object (acts as context manager)
    """
    return _open_corpus(corpus_path, save_path=None)


def open_corpus_readwrite(input_path: str, output_path: str) -> Corpus:
    """
    Open a corpus with save capability.

    The input corpus is copied to the output path immediately (with normalization).
    All modifications are tracked and saved on save() or context exit.

    Args:
        input_path: Path to the input corpus directory
        output_path: Path to the output corpus directory (must not exist)

    Returns:
        A Corpus object (acts as context manager)
    """
    return _open_corpus(input_path, save_path=output_path)


def open_corpus_writeonly(save_path: str) -> Corpus:
    """
    Create a blank corpus with save capability.

    Creates an empty corpus that can be populated with documents.
    All modifications are tracked and saved on save() or context exit.

    Args:
        save_path: Path to the output corpus directory (must not exist)

    Returns:
        A Corpus object (acts as context manager)
    """
    return _open_corpus(corpus_path=None, save_path=save_path)


def open_document(document_path: str) -> Document:
    """
    Open a single document (no save capability).

    The document is loaded into memory immediately.

    Args:
        document_path: Path to the .ozdf file or document directory

    Returns:
        A Document object
    """
    return parse_document(document_path)
