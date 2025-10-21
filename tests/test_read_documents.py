"""
Tests for reading OZDF documents.
"""

import ozdf
import pytest


def test_read_simple_document():
    """Test opening a simple document."""
    # Load the example conversation document
    doc = ozdf.open_document('tests/fixtures/read_simple_document/simple.ozdf')
    title = doc.get_block("Title")
    assert title.get_text() == "Simple!"

    normalization_test = doc.get_block("Normalization Test")
    assert normalization_test.get_text() == "Testing that normalization is working."

    paragraph_test = doc.get_block("Paragraph Test")
    assert len(paragraph_test) == 3
    assert paragraph_test[0] == "First"
    assert paragraph_test[1] == "Second"
    assert paragraph_test[2] == "Third"

    list_block_test = doc.get_list_block("List Block Test")
    assert len(list_block_test) == 2
    assert list_block_test[0].get_name() == 'Named'
    assert list_block_test[0][0] == 'a'
    assert list_block_test[0][1] == 'b'
    assert not list_block_test[1].get_name()
    assert list_block_test[1][0] == 'c'
    assert list_block_test[1][1] == 'd'


def test_read_directory_document():
    """Test opening a directory document with external list blocks."""
    # Load the directory document
    doc = ozdf.open_document('tests/fixtures/read_directory_document/directory_doc')

    # Check that it's a directory document
    assert doc.is_directory() == True

    # Check regular blocks
    assert doc.get_block('Title').get_text() == 'Directory Document Test'
    assert doc.get_block('Description').get_text() == 'This is a test directory document with external list blocks.'
    assert doc.get_block('Author').get_text() == 'Test Author'

    # Check external list block
    messages = doc.get_list_block('Messages')
    assert messages.is_external() == True

    # Check that list items were populated from data parts
    assert len(messages) == 3

    # Check first message (from MESSAGES-01.ozdp)
    assert messages[0].get_name() == 'Alice'
    assert len(messages[0]) == 2
    assert messages[0][0] == 'Hello from Alice!'
    assert messages[0][1] == 'This is a multi-paragraph message.'

    # Check second message (from MESSAGES-02.ozdp)
    assert messages[1].get_name() == 'Bob'
    assert len(messages[1]) == 1
    assert messages[1][0] == 'Hello from Bob!'

    # Check third message (from MESSAGES-03.ozdp)
    assert messages[2].get_name() == 'Charlie'
    assert len(messages[2]) == 1
    assert messages[2][0] == 'Hello from Charlie!'

    # Check non-external list block
    tags = doc.get_list_block('Tags')
    assert tags.is_external() == False
    assert len(tags) == 3
    assert tags[0].get_name() == 'Important'
    assert tags[0].get_text() == 'This document is marked as important for testing purposes.'
    assert tags[1].get_name() == 'Test'
    assert tags[1].get_text() == 'This is a test tag with some description.'
    assert tags[2].get_name() == 'Example'
    assert tags[2].get_text() == 'An example tag to demonstrate non-external list blocks in directory documents.'


def test_directory_document_with_writing_marker():
    """Test that opening a directory document with .ozdf_writing marker raises an error."""
    # Attempting to open should raise ValueError
    with pytest.raises(ValueError, match='contains .ozdf_writing marker'):
        ozdf.open_document('tests/fixtures/corrupted_directory_document')


def test_corpus_with_directory_document_with_writing_marker():
    """Test that opening a corpus with a directory document containing .ozdf_writing marker raises an error."""
    # Attempting to open corpus should raise ValueError
    with pytest.raises(ValueError, match='contains .ozdf_writing marker'):
        ozdf.open_corpus_readonly('tests/fixtures/corpus_with_corrupted_document')

def test_corpus_with_directory_document_with_only_writing_marker():
    """Test that opening a corpus with a directory document containing *only* .ozdf_writing marker raises an error."""
    # Attempting to open corpus should raise ValueError
    with pytest.raises(ValueError, match='contains .ozdf_writing marker'):
        ozdf.open_corpus_readonly('tests/fixtures/corpus_with_corrupted_document_only_writing_marker')
