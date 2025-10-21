"""
Tests for 80-character line wrapping during serialization.
"""

import ozdf


def test_long_paragraph_wraps_at_80_chars(tmp_path):
    """Test that long paragraphs are wrapped at 80 characters when saved."""
    corpus_path = tmp_path / 'corpus'
    with ozdf.open_corpus_writeonly(str(corpus_path)) as corpus:
        doc = corpus.add_document('test.ozdf')
        block = doc.add_block_last('TEST')

        # Add a paragraph that's longer than 80 characters
        long_text = 'This is a very long paragraph that should definitely be wrapped at 80 characters because it contains many words and exceeds the maximum line length that we want to enforce in our output files.'
        block.set_text(long_text)

    # Read the file and check line lengths
    file_path = corpus_path / 'test.ozdf'
    with open(file_path, 'r') as f:
        lines = f.readlines()

        # Skip the header line and blank lines, check content lines
        content_lines = [line.rstrip('\n') for line in lines if line.strip() and not line.startswith('####')]

        # All content lines should be 80 characters or less
        for line in content_lines:
            assert len(line) <= 80, f"Line exceeds 80 chars: {len(line)} chars - {line}"


def test_word_not_broken_at_80_chars(tmp_path):
    """Test that words are not broken when wrapping at 80 characters."""
    corpus_path = tmp_path / 'corpus'
    with ozdf.open_corpus_writeonly(str(corpus_path)) as corpus:
        doc = corpus.add_document('test.ozdf')
        block = doc.add_block_last('TEST')

        # Create text that would break a word if not handled correctly
        text = 'a' * 75 + ' supercalifragilisticexpialidocious'
        block.set_text(text)

    # Read the file
    file_path = corpus_path / 'test.ozdf'
    with open(file_path, 'r') as f:
        content = f.read()

        # The long word should appear intact on its own line
        assert 'supercalifragilisticexpialidocious' in content


def test_very_long_word_exceeds_80_chars(tmp_path):
    """Test that a word longer than 80 chars with no spaces is not broken."""
    corpus_path = tmp_path / 'corpus'
    with ozdf.open_corpus_writeonly(str(corpus_path)) as corpus:
        doc = corpus.add_document('test.ozdf')
        block = doc.add_block_last('TEST')

        # Create a "word" that's longer than 80 characters
        very_long_word = 'a' * 100
        block.set_text(very_long_word)

    # Read the file
    file_path = corpus_path / 'test.ozdf'
    with open(file_path, 'r') as f:
        lines = f.readlines()

        # Find the content line (not header, not blank)
        content_lines = [line.rstrip('\n') for line in lines if line.strip() and not line.startswith('####')]

        # Should be exactly one line with the full word (exception to 80-char rule)
        assert len(content_lines) == 1
        assert len(content_lines[0]) == 100
        assert content_lines[0] == 'a' * 100


def test_list_item_wraps_at_80_chars(tmp_path):
    """Test that list items also wrap at 80 characters."""
    corpus_path = tmp_path / 'corpus'
    with ozdf.open_corpus_writeonly(str(corpus_path)) as corpus:
        doc = corpus.add_document('test.ozdf')
        list_block = doc.add_list_block_last('MYLIST')

        # Add a list item with long text
        long_text = 'This is a very long list item paragraph that should definitely be wrapped at 80 characters because it contains many words and exceeds the maximum line length.'
        list_block.add_list_item('item1', long_text)

    # Read the file and check line lengths
    file_path = corpus_path / 'test.ozdf'
    with open(file_path, 'r') as f:
        lines = f.readlines()

        # Skip headers and blank lines
        content_lines = [line.rstrip('\n') for line in lines if line.strip() and not line.startswith('####') and not line.startswith('====')]

        # All content lines should be 80 characters or less
        for line in content_lines:
            assert len(line) <= 80, f"Line exceeds 80 chars: {len(line)} chars"
