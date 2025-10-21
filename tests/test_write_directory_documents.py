"""
Tests for writing directory documents.
"""

import ozdf
import pytest
from pathlib import Path
from ozdf.models import DirectoryDocument


def test_save_directory_document(tmp_path):
    """Test that directory documents can be saved and reloaded correctly."""

    # Read a corpus containing a directory document
    input_path = 'tests/fixtures/save_directory_document/corpus1'
    output_path = tmp_path / "corpus1"

    # Open corpus in readwrite mode
    with ozdf.open_corpus_readwrite(input_path, str(output_path)) as corpus:
        # Make a small change to verify dirty tracking works
        doc = list(corpus)[0]
        doc.get_block('Title').set_text('Modified Directory Document')
        # Auto-save on exit

    # Read back the saved corpus
    saved_corpus = ozdf.open_corpus_readonly(str(output_path))
    assert len(saved_corpus) == 1

    saved_doc = list(saved_corpus)[0]

    # Verify it's still a directory document
    assert saved_doc.is_directory() == True

    # Verify the modification was saved
    assert saved_doc.get_block('Title').get_text() == 'Modified Directory Document'

    # Verify other metadata blocks
    assert saved_doc.get_block('Description').get_text() == 'Test directory document for saving'
    assert saved_doc.get_block('Author').get_text() == 'Test Author'

    # Verify external list block structure is preserved
    messages = saved_doc.get_list_block('Messages')
    assert messages.is_external() == True

    # Verify external list items were saved correctly
    assert len(messages) == 2
    assert messages[0].get_name() == 'Alice'
    assert messages[0].get_text() == 'Hello from Alice!'
    assert messages[1].get_name() == 'Bob'
    assert messages[1].get_text() == 'Hello from Bob!'

    # Verify non-external list block is preserved
    tags = saved_doc.get_list_block('Tags')
    assert tags.is_external() == False
    assert len(tags) == 2
    assert tags[0].get_name() == 'Important'
    assert tags[0].get_text() == 'This is important.'
    assert tags[1].get_name() == 'Test'
    assert tags[1].get_text() == 'This is a test.'

    # Verify the directory structure on disk
    doc_dir = Path(output_path) / saved_doc.filename
    assert doc_dir.is_dir()
    assert (doc_dir / '_metadata.ozdf').exists()
    assert (doc_dir / 'MESSAGES-01.ozdp').exists()
    assert (doc_dir / 'MESSAGES-02.ozdp').exists()


def test_different_length_external_list_blocks(tmp_path):
    """Test that external list blocks can have different lengths in the new design."""

    # Create a new directory document
    doc = DirectoryDocument('test_doc')

    # Add metadata blocks
    doc.add_block_last('Title', 'Test Document')

    # Add two external list blocks with different lengths - this is now allowed!
    messages = doc.add_external_list_block_last('Messages')
    messages.add_list_item('Alice', 'Hello from Alice')
    messages.add_list_item('Bob', 'Hello from Bob')

    notes = doc.add_external_list_block_last('Notes')
    notes.add_list_item('Note1', 'First note')
    # Only one item - different length is OK now

    # This should succeed
    doc.save_to(str(tmp_path))

    # Verify the saved document is correct
    saved_doc = ozdf.open_document(str(tmp_path / 'test_doc'))
    assert saved_doc.is_directory()

    # Verify both external list blocks were saved correctly with different lengths
    saved_messages = saved_doc.get_list_block('Messages')
    assert len(saved_messages) == 2
    assert saved_messages[0].get_name() == 'Alice'
    assert saved_messages[1].get_name() == 'Bob'

    saved_notes = saved_doc.get_list_block('Notes')
    assert len(saved_notes) == 1
    assert saved_notes[0].get_name() == 'Note1'
    assert saved_notes[0].get_text() == 'First note'

    # Verify correct .ozdp files were created
    doc_dir = tmp_path / 'test_doc'
    assert (doc_dir / 'MESSAGES-01.ozdp').exists()
    assert (doc_dir / 'MESSAGES-02.ozdp').exists()
    assert (doc_dir / 'NOTES-01.ozdp').exists()
    assert not (doc_dir / 'NOTES-02.ozdp').exists()  # Only 1 item


def test_empty_external_list_blocks(tmp_path):
    """Test that directory documents with empty external list blocks can be saved."""

    # Create a new directory document with empty external list blocks
    doc = DirectoryDocument('test_doc')

    doc.add_block_last('Title', 'Empty Document')

    # Add an empty external list block
    messages = doc.add_external_list_block_last('Messages')
    # Don't add any items

    # This should succeed and create only metadata file, no data parts
    doc.save_to(str(tmp_path))

    # Verify the saved document
    doc_dir = tmp_path / 'test_doc'
    assert doc_dir.is_dir()
    assert (doc_dir / '_metadata.ozdf').exists()

    # Should have no .ozdp files since list block is empty
    ozdp_files = list(doc_dir.glob('*.ozdp'))
    assert len(ozdp_files) == 0

    # Verify we can read it back
    saved_doc = ozdf.open_document(str(tmp_path / 'test_doc'))
    assert saved_doc.is_directory()
    assert len(saved_doc.get_list_block('Messages')) == 0


def test_filename_normalization(tmp_path):
    """Test that list block names with spaces are normalized to underscores in filenames."""

    # Create a new directory document
    doc = DirectoryDocument('test_doc')

    doc.add_block_last('Title', 'Test Document')

    # Add an external list block with spaces in the name
    chat_messages = doc.add_external_list_block_last('Chat Messages')
    chat_messages.add_list_item('Alice', 'Hello!')
    chat_messages.add_list_item('Bob', 'Hi there!')

    # Save the document
    doc.save_to(str(tmp_path))

    # Verify the filenames have spaces replaced with underscores and are uppercase
    doc_dir = tmp_path / 'test_doc'
    assert (doc_dir / 'CHAT_MESSAGES-01.ozdp').exists()
    assert (doc_dir / 'CHAT_MESSAGES-02.ozdp').exists()

    # Verify we can read it back correctly
    saved_doc = ozdf.open_document(str(tmp_path / 'test_doc'))
    saved_messages = saved_doc.get_list_block('Chat Messages')
    assert len(saved_messages) == 2
    assert saved_messages[0].get_name() == 'Alice'
    assert saved_messages[1].get_name() == 'Bob'


def test_index_padding(tmp_path):
    """Test that index padding adjusts based on the number of items."""

    # Test 1: Small number of items (< 100) - should use 2 digits
    doc1 = DirectoryDocument('test_doc_2digits')
    doc1.add_block_last('Title', 'Small Document')
    messages1 = doc1.add_external_list_block_last('Messages')
    for i in range(5):
        messages1.add_list_item(f'User{i}', f'Message {i}')
    doc1.save_to(str(tmp_path))

    doc_dir1 = tmp_path / 'test_doc_2digits'
    assert (doc_dir1 / 'MESSAGES-01.ozdp').exists()
    assert (doc_dir1 / 'MESSAGES-05.ozdp').exists()
    # Verify no extra padding
    ozdp_files = sorted(doc_dir1.glob('MESSAGES-*.ozdp'))
    assert ozdp_files[0].name == 'MESSAGES-01.ozdp'
    assert ozdp_files[4].name == 'MESSAGES-05.ozdp'

    # Test 2: Exactly 100 items - should use 3 digits
    doc2 = DirectoryDocument('test_doc_3digits')
    doc2.add_block_last('Title', 'Medium Document')
    messages2 = doc2.add_external_list_block_last('Messages')
    for i in range(100):
        messages2.add_list_item(f'User{i}', f'Message {i}')
    doc2.save_to(str(tmp_path))

    doc_dir2 = tmp_path / 'test_doc_3digits'
    assert (doc_dir2 / 'MESSAGES-001.ozdp').exists()
    assert (doc_dir2 / 'MESSAGES-050.ozdp').exists()
    assert (doc_dir2 / 'MESSAGES-100.ozdp').exists()

    # Verify we can read them all back correctly
    saved_doc1 = ozdf.open_document(str(tmp_path / 'test_doc_2digits'))
    assert len(saved_doc1.get_list_block('Messages')) == 5

    saved_doc2 = ozdf.open_document(str(tmp_path / 'test_doc_3digits'))
    assert len(saved_doc2.get_list_block('Messages')) == 100
