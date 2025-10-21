"""
Tests for reading OZDF corpus.
"""

import ozdf


def test_read_corpus():
    """Test opening a corpus with multiple documents."""
    c = ozdf.open_corpus_readonly('tests/fixtures/read_corpus/test_corpus1')

    # Check that we loaded 2 documents
    assert len(c) == 2

    # Find documents by their title
    doc1 = [d for d in c if d.get_block('Title').get_text() == 'Doc 1'][0]
    doc2 = [d for d in c if d.get_block('Title').get_text() == 'Doc 2'][0]

    # Test document 1 structure
    assert doc1.get_block('Title').get_text() == 'Doc 1'

    # Check paragraphs block
    paragraphs = doc1.get_block('Paragraphs')
    assert len(paragraphs) == 2
    assert paragraphs[0] == 'P1'
    assert paragraphs[1] == 'P2'

    # Check list block
    list_block = doc1.get_list_block('List Block')
    assert len(list_block) == 2

    # First list item (unnamed)
    assert list_block[0].get_name() is None
    assert len(list_block[0]) == 2
    assert list_block[0][0] == 'L1P1'
    assert list_block[0][1] == 'L1P2'

    # Second list item (unnamed)
    assert list_block[1].get_name() is None
    assert len(list_block[1]) == 2
    assert list_block[1][0] == 'L2P1'
    assert list_block[1][1] == 'L2P2'

    # Test document 2 structure
    assert doc2.get_block('Title').get_text() == 'Doc 2'

    # Check paragraphs block
    paragraphs2 = doc2.get_block('Paragraphs')
    assert len(paragraphs2) == 1
    assert paragraphs2[0] == 'Only 1 paragraph here'

    # Check list block with named item
    list_block2 = doc2.get_list_block('List Block')
    assert len(list_block2) == 1
    assert list_block2[0].get_name() == 'I got a name'
    assert len(list_block2[0]) == 1
    assert list_block2[0][0] == "This list block has only 1 item. And it's named!"


def test_corpus_iteration():
    """Test that corpus is iterable."""
    c = ozdf.open_corpus_readonly('tests/fixtures/corpus_iteration/test_corpus1')

    count = 0
    for doc in c:
        count += 1
        assert isinstance(doc, ozdf.Document)
    assert count == 2
