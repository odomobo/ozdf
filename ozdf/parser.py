"""
Parsing logic for OZDF files.

This module handles parsing of:
- Simple .ozdf document files
- Directory documents
- .ozdp data part files
"""

import os
import re
import glob
from typing import Tuple, List, Dict, Optional, Union
from ozdf.models import Document, DirectoryDocument, Block, ListBlock, ListItem, Comment, ExternalListBlock


class _TextBuilder:
    """Helper class to accumulate lines and build text content for a block, list item, or comment."""

    def __init__(self, target: Union[Block, ListItem, Comment]):
        """
        Initialize a TextBuilder.

        Args:
            target: The Block, ListItem, or Comment object to populate
        """
        self.target = target
        self.lines: List[str] = []

    def append(self, line: str):
        """
        Append a line to the accumulated content.

        Args:
            line: A line of text from the file
        """
        self.lines.append(line)

    def apply(self):
        """
        Process the accumulated lines and call set_text() on the target.
        """
        # Join all lines
        text = '\n'.join(self.lines)
        # Call set_text on the target (Block or ListItem)
        self.target.set_text(text)


def parse_document(file_path: str) -> Document:
    """
    Parse a .ozdf document file or directory document.

    Args:
        file_path: Path to the .ozdf file or directory

    Returns:
        A Document object
    """
    # Check if it's a directory or file
    is_directory = os.path.isdir(file_path)

    # Create document of appropriate type
    if is_directory:
        # Check if .ozdf_writing marker exists - this indicates a corrupted/incomplete write
        writing_marker = os.path.join(file_path, '.ozdf_writing')
        if os.path.exists(writing_marker):
            raise ValueError(f"Directory document '{file_path}' contains .ozdf_writing marker, indicating an incomplete or corrupted save operation")
        
        doc = DirectoryDocument(file_path)
    else:
        doc = Document(file_path)

    # Determine actual file to read
    if is_directory:
        actual_file_path = os.path.join(file_path, '_metadata.ozdf')
    else:
        actual_file_path = file_path

    with open(actual_file_path, 'r', encoding='utf-8') as f:
        builder: Optional[_TextBuilder] = None
        current_list_block: Optional[ListBlock] = None
        prev_line_was_blank = False
        blank_line_required = False  # First header doesn't need blank line before it

        for line in f:
            stripped = line.strip()

            # Check if this is a block header
            if stripped.startswith('#### '):
                # Check for blank line requirement
                if blank_line_required and not prev_line_was_blank:
                    raise ValueError(f"Headers must be preceded by a blank line in '{file_path}'")

                # Finish previous element
                if builder:
                    builder.apply()
                    builder = None

                header = stripped[5:].strip()  # Remove "#### " prefix

                # Check if it's an external list block [[Name]]
                if header.startswith('[[') and header.endswith(']]'):
                    # External list blocks are only allowed in directory documents
                    if not isinstance(doc, DirectoryDocument):
                        raise ValueError(f"External list blocks [[Name]] are only allowed in directory documents, not in '{actual_file_path}'")

                    list_name = header[2:-2]  # Extract name from double brackets
                    # Create empty ExternalListBlock and populate it from .ozdp files
                    external_list_block = doc.add_external_list_block_last(list_name)
                    populate_external_list_block(file_path, external_list_block)
                    current_list_block = None
                    blank_line_required = True
                # Check if it's a regular list block [Name]
                elif header.startswith('[') and header.endswith(']'):
                    list_name = header[1:-1]  # Extract name from brackets
                    current_list_block = doc.add_list_block_last(list_name)
                    blank_line_required = False  # First list item doesn't need blank line
                elif header.upper() == 'COMMENT':
                    current_list_block = None
                    comment = doc._add_comment_last()
                    builder = _TextBuilder(comment)
                    blank_line_required = True
                else:
                    current_list_block = None
                    block = doc.add_block_last(header)
                    builder = _TextBuilder(block)
                    blank_line_required = True

            # we need to properly handle unnamed list items
            elif stripped == '====' or stripped.startswith('==== '):
                # Check if we're inside a list block
                if current_list_block is None:
                    raise ValueError(f"List item header found outside of list block in '{file_path}'")

                # Check for blank line requirement
                if blank_line_required and not prev_line_was_blank:
                    raise ValueError(f"List item headers must be preceded by a blank line in '{file_path}'")

                # This is a list item header
                if builder:
                    builder.apply()

                item_name_part = stripped[5:].strip()  # Remove "==== " prefix
                item_name = item_name_part if item_name_part else None

                # Create list item and add to current list block
                list_item = current_list_block.add_list_item(item_name)
                builder = _TextBuilder(list_item)
                blank_line_required = True  # Next list item DOES need blank line

            elif stripped.startswith('###') or stripped.startswith('==='):
                # Invalid line - starts with ### or === but not a valid header
                raise ValueError(f"Invalid line in file '{file_path}': lines cannot start with '###' or '===' unless they are headers")

            else:
                # This is content for the current element (or blank line)
                if builder:
                    builder.append(stripped)
                elif stripped:  # Non-empty content before first header
                    raise ValueError(f"Content found before first header in '{file_path}'")

            # Update blank line tracking
            prev_line_was_blank = (stripped == '')

        # Don't forget the last element
        if builder:
            builder.apply()

    return doc


def parse_data_part_file(file_path: str) -> Document:
    """
    Parse a .ozdp data part file.

    Args:
        file_path: Path to the .ozdp file

    Returns:
        The data part document
    """
    doc = Document(file_path)

    with open(file_path, 'r', encoding='utf-8') as f:
        builder: Optional[_TextBuilder] = None
        prev_line_was_blank = False
        blank_line_required = False  # First header doesn't need blank line before it

        for line in f:
            stripped = line.strip()

            # Check if this is a block header
            if stripped.startswith('#### '):
                # Check for blank line requirement
                if blank_line_required and not prev_line_was_blank:
                    raise ValueError(f"Headers must be preceded by a blank line in '{file_path}'")

                # Finish previous element
                if builder:
                    builder.apply()
                    builder = None

                header = stripped[5:].strip()  # Remove "#### " prefix

                # Check if it's a comment
                if header.upper() == 'COMMENT':
                    comment = doc._add_comment_last()
                    builder = _TextBuilder(comment)
                    blank_line_required = True
                else:
                    # Data part files contain simple blocks
                    block = doc.add_block_last(header)
                    builder = _TextBuilder(block)
                    blank_line_required = True

            elif stripped.startswith('###') or stripped.startswith('==='):
                # Invalid line - starts with ### or === but not a valid header
                raise ValueError(f"Invalid line in data part file '{file_path}': lines cannot start with '###' or '===' unless they are headers")

            else:
                # This is content for the current element (or blank line)
                if builder:
                    builder.append(stripped)
                elif stripped:  # Non-empty content before first header
                    raise ValueError(f"Content found before first header in '{file_path}'")

            # Update blank line tracking
            prev_line_was_blank = (stripped == '')

        # Don't forget the last element
        if builder:
            builder.apply()

    return doc


def populate_external_list_block(dir_path: str, list_block: ExternalListBlock):
    """
    Populate an external list block by scanning for and parsing its .ozdp files.

    Args:
        dir_path: Path to the directory containing the .ozdp files
        list_block: The ExternalListBlock to populate

    Raises:
        ValueError: If .ozdp files are missing required DATA block or have invalid format
    """
    # Normalize the list block name for filenames (uppercase, spaces → underscores)
    normalized_name = list_block.name.upper().replace(' ', '_')

    # Pattern to match files: {NORMALIZED_NAME}-{digits}.ozdp
    pattern = f"{normalized_name}-*.ozdp"

    # Find all matching .ozdp files in the directory
    file_pattern = os.path.join(dir_path, pattern)
    matching_files = glob.glob(file_pattern)

    if not matching_files:
        # No data parts found - this is valid, just means empty external list block
        return

    # Extract index from filename and create (index, filepath) tuples
    indexed_files = []
    filename_pattern = re.compile(rf'^{re.escape(normalized_name)}-(\d+)\.ozdp$')

    for file_path in matching_files:
        filename = os.path.basename(file_path)
        match = filename_pattern.match(filename)

        if not match:
            raise ValueError(f"Invalid .ozdp filename format: '{filename}' (expected {normalized_name}-<digits>.ozdp)")

        index = int(match.group(1))
        indexed_files.append((index, file_path))

    # Sort by index
    indexed_files.sort(key=lambda x: x[0])

    # Validate indexes are contiguous starting from 1
    for i, (index, file_path) in enumerate(indexed_files):
        expected_index = i + 1
        if index != expected_index:
            filename = os.path.basename(file_path)
            raise ValueError(f"Data part indexes must be contiguous starting from 1. Expected {expected_index}, got {index} in '{filename}'")

    # Process each file in order
    for index, file_path in indexed_files:
        # Parse the .ozdp file
        data_part_doc = parse_data_part_file(file_path)

        # Extract NAME block if present (optional)
        item_name = None
        try:
            name_block = data_part_doc.get_block('NAME')
            item_name = name_block.get_text()
        except KeyError:
            # No NAME block - that's fine, item will have no name
            pass

        # Extract DATA block (required)
        try:
            data_block = data_part_doc.get_block('DATA')
        except KeyError:
            raise ValueError(f"Data part file '{file_path}' missing required DATA block")

        item_text = data_block.get_text()

        # Create list item and add to external list block
        list_item = list_block.add_list_item(item_name)
        list_item.set_text(item_text)
