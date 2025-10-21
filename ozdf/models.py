"""
Core data model classes for OZDF.

This module contains the main data structures:
- Corpus: A collection of documents
- Document: Contains blocks and list blocks
- Block: A simple text block with paragraphs
- ListBlock: A block containing list items
- ListItem: Contains paragraphs, supports indexing
"""

import os
import glob
import shutil
from typing import List, Optional, Iterator

from ozdf.normalization import split_into_paragraphs, normalize_paragraphs, wrap_to_80_chars


class Block:
    """A simple text block containing one or more paragraphs."""

    def __init__(self, name: str, parent: 'Document'):
        """
        Initialize a Block.

        Args:
            name: The block name (will be converted to uppercase)
            parent: The parent Document
        """
        self.name = name.upper()
        self.paragraphs: List[str] = []
        self._parent = parent

    def _mark_dirty(self):
        """Mark this block's parent document as dirty."""
        self._parent._mark_dirty()

    def get_text(self) -> str:
        """Get the full text of the block with paragraphs separated by double newlines."""
        return "\n\n".join(self.paragraphs)

    def set_text(self, text: str):
        """
        Set the text content of the block, separating into paragraphs and normalizing.

        Paragraphs are separated by blank lines (one or more empty lines).
        Text is normalized (whitespace collapsed, etc.).

        Args:
            text: The text content to set
        """
        paragraphs = split_into_paragraphs(text)
        self.paragraphs = normalize_paragraphs(paragraphs)
        self._mark_dirty()

    def set_paragraphs(self, paragraphs: List[str]):
        """
        Set the paragraphs directly from a list.

        Args:
            paragraphs: List of paragraph strings
        """
        self.paragraphs = list(paragraphs)  # Make a copy
        self._mark_dirty()

    def __iter__(self) -> Iterator[str]:
        """Iterate over paragraphs."""
        return iter(self.paragraphs)

    def __len__(self) -> int:
        """Return the number of paragraphs."""
        return len(self.paragraphs)

    def __getitem__(self, index: int) -> str:
        """Get a paragraph by index."""
        return self.paragraphs[index]

    def __setitem__(self, index: int, value: str):
        """Set a paragraph by index."""
        self.paragraphs[index] = value
        self._mark_dirty()

    def append(self, paragraph: str):
        """Add a paragraph to the end of the block."""
        self.paragraphs.append(paragraph)
        self._mark_dirty()

    def _serialize_to(self, file):
        """
        Serialize this block to a file. Also normalizes paragraphs.

        Args:
            file: A file-like object opened for writing
        """
        # Normalize paragraphs first
        self.paragraphs = normalize_paragraphs(self.paragraphs)

        # Write block header
        file.write(f"#### {self.name}\n")

        # Write each paragraph separated by blank lines
        for i, paragraph in enumerate(self.paragraphs):
            wrapped = wrap_to_80_chars(paragraph)
            file.write(wrapped)
            file.write("\n\n")

        # Add required double newline if one wasn't added by writing the paragraphs
        if not self.paragraphs:
            file.write("\n\n")


# Note: Comment type is excluded from cheatsheet
class Comment:
    """A comment block that stores raw text without normalization."""

    def __init__(self):
        """
        Initialize a Comment.

        Args:
            parent: The parent Document (optional)
        """
        self.text: str = ""

    def set_text(self, text: str):
        """
        Set the text content of the comment.

        Does NOT normalize - stores raw text as-is.

        Args:
            text: The text content to set
        """
        self.text = text

    def _serialize_to(self, file):
        """
        Serialize this comment to a file.

        Args:
            file: A file-like object opened for writing
        """
        # Write comment header
        file.write("#### COMMENT\n")

        # Write raw text as-is
        file.write(self.text)

        # Add newline that got lost when building self.text
        file.write("\n")


class ListItem(Block):
    """A list item containing one or more paragraphs. Supports indexing and iteration."""

    def __init__(self, name: Optional[str], parent: 'Document'):
        """
        Initialize a ListItem.

        Args:
            name: The optional list item name (NOT converted to uppercase, unlike Block)
            parent: The parent Document
        """
        # Don't call super().__init__() because Block uppercases the name
        # Instead, directly set the name, paragraphs, and parent
        self.name = name
        self.paragraphs: List[str] = []
        self._parent = parent

    def get_name(self) -> Optional[str]:
        """
        Get the name of the list item.

        Returns:
            The list item name, or None if unnamed
        """
        return self.name

    def _serialize_to(self, file):
        """
        Serialize this list item to a file. Also normalizes paragraphs.

        Args:
            file: A file-like object opened for writing
        """
        # Normalize paragraphs first
        self.paragraphs = normalize_paragraphs(self.paragraphs)

        # Write list item header
        if self.name:
            file.write(f"==== {self.name}\n")
        else:
            file.write("====\n")

        # Write each paragraph separated by blank lines
        for i, paragraph in enumerate(self.paragraphs):
            wrapped = wrap_to_80_chars(paragraph)
            file.write(wrapped)
            file.write("\n\n")

        # Add required double newline if one wasn't added by writing the paragraphs
        if not self.paragraphs:
            file.write("\n\n")


class ListBlock:
    """A list block containing one or more list items."""

    def __init__(self, name: str, parent: 'Document'):
        """
        Initialize a ListBlock.

        Args:
            name: The list block name (will be converted to uppercase)
            parent: The parent Document
        """
        self.name = name.upper()
        self.items: List[ListItem] = []
        self._parent = parent

    def _mark_dirty(self):
        """Mark this list block's parent document as dirty."""
        self._parent._mark_dirty()

    def is_external(self) -> bool:
        """
        Check if this is an external list block.

        Returns:
            False for regular ListBlock, True for ExternalListBlock
        """
        return False

    def add_list_item(self, name: Optional[str] = None, content: str = "") -> ListItem:
        """
        Add a list item to this list block.

        Args:
            name: Optional name for the list item
            content: The text content for the list item (default: empty string)

        Returns:
            The newly created ListItem object
        """
        list_item = ListItem(name, parent=self._parent)
        if content:
            list_item.set_text(content)
        self.items.append(list_item)
        self._mark_dirty()
        return list_item

    def set_list_items(self, items):
        """
        Set the list items from an iterable.

        Args:
            items: An iterable of ListItem objects

        Raises:
            ValueError: If any list item's parent is not this ListBlock's parent document
        """
        items_list = list(items)  # Make a copy

        # Validate that each item's parent is our parent document
        for item in items_list:
            if item._parent is not self._parent:
                raise ValueError(f"List item parent mismatch: expected parent document, but item has different parent")

        self.items = items_list
        self._mark_dirty()

    def __iter__(self) -> Iterator[ListItem]:
        """Iterate over list items."""
        return iter(self.items)

    def __len__(self) -> int:
        """Return the number of list items."""
        return len(self.items)

    def __getitem__(self, index: int) -> ListItem:
        """Get a list item by index."""
        return self.items[index]

    def _serialize_to(self, file):
        """
        Serialize this list block to a file.

        Args:
            file: A file-like object opened for writing
        """
        # Write list block header
        file.write(f"#### [{self.name}]\n")

        # Write each list item
        for item in self.items:
            item._serialize_to(file)


class ExternalListBlock(ListBlock):
    """An external list block for directory documents. Items are populated from .ozdp files."""

    def __init__(self, name: str, parent: 'Document'):
        """
        Initialize an ExternalListBlock.

        Args:
            name: The list block name (will be converted to uppercase)
            parent: The parent Document
        """
        super().__init__(name, parent)

    def is_external(self) -> bool:
        """
        Check if this is an external list block.

        Returns:
            True for ExternalListBlock
        """
        return True

    def _serialize_to(self, file):
        """
        Serialize this external list block to a file (writes just the header, not items).

        Args:
            file: A file-like object opened for writing
        """
        # Write external list block header
        file.write(f"#### [[{self.name}]]\n")

        # Write trailing blank line
        file.write("\n")

    def _save_data_parts_to(self, directory: str):
        """
        Save all list items as individual .ozdp files in the specified directory.

        Args:
            directory: The directory path where .ozdp files should be saved
        """
        # Normalize the list block name for filenames (uppercase, spaces → underscores)
        normalized_name = self.name.upper().replace(' ', '_')

        # Note: .ozdp files must be removed by the caller before calling this method

        # If no items, we're done
        if not self.items:
            return

        # Calculate index padding (number of digits needed based on total items)
        num_items = len(self.items)
        padding = max(2, len(str(num_items)))  # At least 2 digits

        # Save each list item as a separate .ozdp file
        for index, list_item in enumerate(self.items, start=1):
            # Create filename with padded index
            padded_index = str(index).zfill(padding)
            filename = f"{normalized_name}-{padded_index}.ozdp"
            file_path = os.path.join(directory, filename)

            # Write the .ozdp file
            with open(file_path, 'w', encoding='utf-8') as f:
                # Write NAME block if the list item has a name
                if list_item.name:
                    f.write("#### NAME\n")
                    f.write(f"{list_item.name}\n")
                    f.write("\n")

                # Write DATA block (always present)
                f.write("#### DATA\n")
                f.write(f"{list_item.get_text()}\n")
                f.write("\n")

class Document:
    """A document containing blocks and list blocks."""

    def __init__(self, file_path: str):
        """
        Initialize a Document.

        Args:
            file_path: Path to the source file
        """
        self.filename = os.path.basename(file_path)
        self._blocks: dict = {}  # Maps uppercase block names to Block objects
        self._list_blocks: dict = {}  # Maps uppercase list block names to ListBlock objects
        self._ordered_elements: List = []  # Track order of all elements (blocks, list blocks, comments)
        self._dirty = True

    def _mark_dirty(self):
        """Mark this document as dirty (modified)."""
        self._dirty = True

    def get_block(self, name: str) -> Block:
        """
        Get a block by name (case-insensitive).

        Args:
            name: The block name

        Returns:
            The Block object

        Raises:
            KeyError: If block with the given name does not exist
        """
        upper_name = name.upper()
        if upper_name not in self._blocks:
            raise KeyError(f"Block '{name}' not found in document '{self.filename}'")
        return self._blocks[upper_name]

    def get_list_block(self, name: str) -> ListBlock:
        """
        Get a list block by name (case-insensitive).

        Args:
            name: The list block name

        Returns:
            The ListBlock object

        Raises:
            KeyError: If list block with the given name does not exist
        """
        upper_name = name.upper()
        if upper_name not in self._list_blocks:
            raise KeyError(f"List block '{name}' not found in document '{self.filename}'")
        return self._list_blocks[upper_name]

    def _add_block(self, name: str, content: str, position: int) -> Block:
        """
        Internal method to add a block at a specific position.

        Args:
            name: The block name
            content: The block content
            position: Index position in _ordered_elements (0 for first, -1 for last)

        Returns:
            The newly created Block object

        Raises:
            ValueError: If a block with this name already exists
        """
        # Convert name to uppercase for storage (case-insensitive lookups)
        upper_name = name.upper()

        # Check if block already exists
        if upper_name in self._blocks:
            raise ValueError(f"Block '{name}' already exists in document '{self.filename}'")

        # Create the block with parent reference
        block = Block(name, parent=self)

        # Set content if provided
        if content:
            block.set_text(content)

        # Store in blocks dict
        self._blocks[upper_name] = block

        # Add to order tracking at specified position
        if position == -1:
            self._ordered_elements.append(block)
        else:
            self._ordered_elements.insert(position, block)

        # Mark document as dirty
        self._mark_dirty()

        return block

    def add_block_first(self, name: str, content: str = "") -> Block:
        """
        Add a block at the beginning of the document.

        Args:
            name: The block name
            content: The block content (default: empty string)

        Returns:
            The newly created Block object
        """
        return self._add_block(name, content, position=0)

    def add_block_last(self, name: str, content: str = "") -> Block:
        """
        Add a block at the end of the document.

        Args:
            name: The block name
            content: The block content (default: empty string)

        Returns:
            The newly created Block object
        """
        return self._add_block(name, content, position=-1)

    def remove_block(self, name: str):
        """
        Remove a block by name (case-insensitive).

        Args:
            name: The block name to remove

        Raises:
            KeyError: If block with the given name does not exist
        """
        # Convert name to uppercase for lookup
        upper_name = name.upper()

        # Check if block exists
        if upper_name not in self._blocks:
            raise KeyError(f"Block '{name}' not found in document '{self.filename}'")

        # Get the block object
        block = self._blocks[upper_name]

        # Remove from blocks dict
        del self._blocks[upper_name]

        # Remove from ordered elements
        self._ordered_elements.remove(block)

        # Mark document as dirty
        self._mark_dirty()

    def _add_list_block(self, name: str, position: int) -> ListBlock:
        """
        Internal method to add a list block at a specific position.

        Args:
            name: The list block name
            position: Index position in _ordered_elements (0 for first, -1 for last)

        Returns:
            The newly created ListBlock object

        Raises:
            ValueError: If a list block with this name already exists
        """
        # Convert name to uppercase for storage (case-insensitive lookups)
        upper_name = name.upper()

        # Check if list block already exists
        if upper_name in self._list_blocks:
            raise ValueError(f"List block '{name}' already exists in document '{self.filename}'")

        # Create the list block with parent reference
        list_block = ListBlock(name, parent=self)

        # Store in list blocks dict
        self._list_blocks[upper_name] = list_block

        # Add to order tracking at specified position
        if position == -1:
            self._ordered_elements.append(list_block)
        else:
            self._ordered_elements.insert(position, list_block)

        # Mark document as dirty
        self._mark_dirty()

        return list_block

    def add_list_block_first(self, name: str) -> ListBlock:
        """
        Add an empty list block at the beginning of the document.

        Args:
            name: The list block name

        Returns:
            The newly created ListBlock object
        """
        return self._add_list_block(name, position=0)

    def add_list_block_last(self, name: str) -> ListBlock:
        """
        Add an empty list block at the end of the document.

        Args:
            name: The list block name

        Returns:
            The newly created ListBlock object
        """
        return self._add_list_block(name, position=-1)

    def remove_list_block(self, name: str):
        """
        Remove a list block by name (case-insensitive).

        Args:
            name: The list block name to remove

        Raises:
            KeyError: If list block with the given name does not exist
        """
        # Convert name to uppercase for lookup
        upper_name = name.upper()

        # Check if list block exists
        if upper_name not in self._list_blocks:
            raise KeyError(f"List block '{name}' not found in document '{self.filename}'")

        # Get the list block object
        list_block = self._list_blocks[upper_name]

        # Remove from list blocks dict
        del self._list_blocks[upper_name]

        # Remove from ordered elements
        self._ordered_elements.remove(list_block)

        # Mark document as dirty
        self._mark_dirty()

    def _add_comment_last(self) -> Comment:
        """
        Add a comment at the end of the document.

        Returns:
            The newly created Comment object
        """
        comment = Comment()
        self._ordered_elements.append(comment)
        self._mark_dirty()
        return comment

    def save_to(self, directory: str):
        """
        Save this document to a directory using its filename.

        Uses atomic write pattern: writes to .tmp file first, then moves to final location.

        Note: Does not clear the dirty flag - that is the caller's responsibility.

        Args:
            directory: The directory where the document should be saved
        """
        # Ensure directory exists
        os.makedirs(directory, exist_ok=True)

        # Construct the full file path and temp path
        file_path = os.path.join(directory, self.filename)
        temp_path = file_path + '.tmp'

        # Write to temporary file first
        with open(temp_path, 'w') as f:
            for element in self._ordered_elements:
                element._serialize_to(f)

        # Atomically move temp file to final location (potentially overwriting)
        os.replace(temp_path, file_path)

    def is_directory(self) -> bool:
        """
        Check if this is a directory document.

        Returns:
            False for regular Document, True for DirectoryDocument
        """
        return False


class DirectoryDocument(Document):
    """A directory document with _metadata.ozdf and .ozdp data part files."""

    def __init__(self, file_path: str):
        """
        Initialize a DirectoryDocument.

        Args:
            file_path: Path to the directory containing _metadata.ozdf
        """
        super().__init__(file_path)

    def is_directory(self) -> bool:
        """
        Check if this is a directory document.

        Returns:
            True for DirectoryDocument
        """
        return True

    def _add_external_list_block(self, name: str, position: int) -> ExternalListBlock:
        """
        Internal method to add an external list block at a specific position.

        Args:
            name: The list block name
            position: Index position in _ordered_elements (0 for first, -1 for last)

        Returns:
            The newly created ExternalListBlock object

        Raises:
            ValueError: If a list block with this name already exists
        """
        # Convert name to uppercase for storage (case-insensitive lookups)
        upper_name = name.upper()

        # Check if list block already exists
        if upper_name in self._list_blocks:
            raise ValueError(f"List block '{name}' already exists in document '{self.filename}'")

        # Create the external list block with parent reference
        external_list_block = ExternalListBlock(name, parent=self)

        # Store in list blocks dict
        self._list_blocks[upper_name] = external_list_block

        # Add to order tracking at specified position
        if position == -1:
            self._ordered_elements.append(external_list_block)
        else:
            self._ordered_elements.insert(position, external_list_block)

        # Mark document as dirty
        self._mark_dirty()

        return external_list_block

    def add_external_list_block_first(self, name: str) -> ExternalListBlock:
        """
        Add an external list block at the beginning of the document.

        Args:
            name: The list block name

        Returns:
            The newly created ExternalListBlock object
        """
        return self._add_external_list_block(name, position=0)

    def add_external_list_block_last(self, name: str) -> ExternalListBlock:
        """
        Add an external list block at the end of the document.

        Args:
            name: The list block name

        Returns:
            The newly created ExternalListBlock object
        """
        return self._add_external_list_block(name, position=-1)

    def save_to(self, directory: str):
        """
        Save this directory document to a directory.

        Saves both _metadata.ozdf and all .ozdp data part files.
        Uses backup/recovery mechanism to ensure data integrity.

        Note: Does not clear the dirty flag - that is the caller's responsibility.

        Args:
            directory: The directory where the document should be saved
        """
        # Ensure parent directory exists
        os.makedirs(directory, exist_ok=True)

        # Construct the directory path for this document
        doc_directory = os.path.join(directory, self.filename)
        os.makedirs(doc_directory, exist_ok=True)

        # Define special file/folder names
        writing_marker = os.path.join(doc_directory, '.ozdf_writing')
        backup_dir = os.path.join(doc_directory, '.ozdf_backup')

        # Step 1: Create .ozdf_writing marker file
        with open(writing_marker, 'w') as f:
            f.write('')  # Empty marker file

        # Step 2: Create .ozdf_backup subfolder
        os.makedirs(backup_dir, exist_ok=True)

        # Step 3: Find all files to back up
        backup_files = []
        for item in os.listdir(doc_directory):
            item_path = os.path.join(doc_directory, item)
            # Skip the marker and backup directory itself
            if item in ('.ozdf_writing', '.ozdf_backup'):
                continue
            # Record file for backup
            if os.path.isfile(item_path):
                backup_files.append(item)

        # Step 4: Move all existing files into .ozdf_backup/
        for item in backup_files:
            src_path = os.path.join(doc_directory, item)
            backup_path = os.path.join(backup_dir, item)
            shutil.move(src_path, backup_path)

        # Step 5: Write all new files
        # Write _metadata.ozdf
        metadata_path = os.path.join(doc_directory, '_metadata.ozdf')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            for element in self._ordered_elements:
                element._serialize_to(f)

        # Write data parts for each external list block
        for element in self._ordered_elements:
            if isinstance(element, ExternalListBlock):
                element._save_data_parts_to(doc_directory)

        # Step 6: Delete .ozdf_writing marker
        os.remove(writing_marker)

        # Step 7: Delete backup files explicitly, then delete .ozdf_backup/ folder
        for backup_file in backup_files:
            backup_path = os.path.join(backup_dir, backup_file)
            os.remove(backup_path)
        os.rmdir(backup_dir)


class Corpus:
    """A collection of documents. Supports iteration and filtering. Acts as a context manager."""

    def __init__(self, save_path: Optional[str] = None):
        """
        Initialize a Corpus.

        Args:
            save_path: Optional path where corpus can be saved (None = no save capability)
        """
        self.documents: List[Document] = []
        self.save_path = save_path

    def _add_existing_document(self, document: Document):
        """
        Internal method to add an existing document to the corpus.

        Args:
            document: The Document object to add
        """
        self.documents.append(document)

    def add_document(self, filename: str) -> Document:
        """
        Create a new document and add it to the corpus.

        Args:
            filename: The filename for the new document (e.g., 'my_doc.ozdf')

        Returns:
            The newly created Document object
        """
        document = Document(filename)
        self.documents.append(document)
        return document

    def add_directory_document(self, dirname: str) -> DirectoryDocument:
        """
        Create a new directory document and add it to the corpus.

        Args:
            dirname: The directory name for the new document (e.g., 'my_doc')

        Returns:
            The newly created DirectoryDocument object
        """
        document = DirectoryDocument(dirname)
        self.documents.append(document)
        return document

    def __iter__(self) -> Iterator[Document]:
        """Iterate over documents."""
        return iter(self.documents)

    def __len__(self) -> int:
        """Return the number of documents."""
        return len(self.documents)

    # Note: __enter__ and __exit__ are excluded from cheatsheet
    def __enter__(self) -> 'Corpus':
        """Enter the context and return self."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and auto-save if save path exists."""
        # Only save if we have a save_path and no exception occurred
        if self.save_path is not None and exc_type is None:
            self.save()
        # Don't suppress any exceptions
        return False

    def save(self):
        """
        Save all dirty documents to disk.

        Raises:
            RuntimeError: If corpus was opened without a save path
        """
        # Check if save_path exists
        if self.save_path is None:
            raise RuntimeError("Cannot save corpus opened in read-only mode")

        # Save all dirty documents
        for document in self.documents:
            if document._dirty:
                document.save_to(self.save_path)
                # Clear dirty flag after successful save
                document._dirty = False
