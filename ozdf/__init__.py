"""
OZDF (Ozone Data Format) - A human-readable format for LLM training data.

This package provides functionality to read, write, and manipulate OZDF files.
"""

from ozdf.io import open_corpus_readonly, open_corpus_readwrite, open_corpus_writeonly, open_document
from ozdf.models import Corpus, Document, DirectoryDocument, Block, ListBlock, ExternalListBlock, ListItem

__all__ = [
    'open_corpus_readonly',
    'open_corpus_readwrite',
    'open_corpus_writeonly',
    'open_document',
    'Corpus',
    'Document',
    'DirectoryDocument',
    'Block',
    'ListBlock',
    'ExternalListBlock',
    'ListItem',
]

__version__ = '0.1.0'
