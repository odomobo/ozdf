"""
Tests for writing OZDF corpus.
"""

import ozdf


def test_create_new_corpus(tmp_path):
    """Test creating a new corpus from scratch and saving."""

    # Define output path
    output_path = tmp_path / "corpus1"

    # Create a new corpus
    with ozdf.open_corpus_writeonly(str(output_path)) as corpus:
        # Create a new document
        doc = corpus.add_document('new_document.ozdf')

        # Add a simple block
        title_block = doc.add_block_last('Title', 'My New Document')

        # Add a paragraphs block with multiple paragraphs
        content_block = doc.add_block_last('Content')
        content_block.append('First paragraph of content.')
        content_block.append('Second paragraph of content.')

        # Add a list block with one item
        list_block = doc.add_list_block_last('Tasks')
        list_item = list_block.add_list_item('First Task')
        list_item.append('This is the description of the first task.')
        list_item.append('It has multiple paragraphs too.')

        # Auto-save happens on context exit

    # Verify the saved corpus by reading it back
    saved_corpus = ozdf.open_corpus_readonly(str(output_path))
    assert len(saved_corpus) == 1

    saved_doc = list(saved_corpus)[0]
    assert saved_doc.get_block('Title').get_text() == 'My New Document'

    content = saved_doc.get_block('Content')
    assert len(content) == 2
    assert content[0] == 'First paragraph of content.'
    assert content[1] == 'Second paragraph of content.'

    tasks = saved_doc.get_list_block('Tasks')
    assert len(tasks) == 1
    assert tasks[0].get_name() == 'First Task'
    assert len(tasks[0]) == 2
    assert tasks[0][0] == 'This is the description of the first task.'
    assert tasks[0][1] == "It has multiple paragraphs too."


def test_modify_existing_corpus(tmp_path):
    """Test opening a corpus in readwrite mode, making changes, and saving."""

    # Define paths
    input_path = 'tests/fixtures/modify_existing_corpus/test_corpus1'
    output_path = tmp_path / "corpus1"

    # Open corpus in readwrite mode
    with ozdf.open_corpus_readwrite(input_path, str(output_path)) as corpus:
        # Find Doc 1 and make changes
        doc1 = [d for d in corpus if d.get_block('Title').get_text() == 'Doc 1'][0]

        # Change the title
        doc1.get_block('Title').set_text('Doc 1 - Modified')

        # Add a paragraph to the Paragraphs block
        paragraphs = doc1.get_block('Paragraphs')
        paragraphs.append('P3 - Added by test')
        corpus.save()

        # Find Doc 2 and make changes
        doc2 = [d for d in corpus if d.get_block('Title').get_text() == 'Doc 2'][0]

        # Modify the paragraph
        doc2.get_block('Paragraphs').set_text('Modified: Only 1 paragraph here')

        list_item = doc2.get_list_block('List Block').add_list_item()
        list_item.append("""Why,
                         hello    there! I'm a new addition to this family.""")

        # Auto-save happens on context exit

    # Verify the saved corpus by reading it back
    saved_corpus = ozdf.open_corpus_readonly(str(output_path))
    assert len(saved_corpus) == 2

    # Verify Doc 1 changes
    saved_doc1 = [d for d in saved_corpus if d.get_block('Title').get_text() == 'Doc 1 - Modified'][0]
    assert saved_doc1.get_block('Title').get_text() == 'Doc 1 - Modified'

    paragraphs1 = saved_doc1.get_block('Paragraphs')
    assert len(paragraphs1) == 3
    assert paragraphs1[0] == 'P1'
    assert paragraphs1[1] == 'P2'
    assert paragraphs1[2] == 'P3 - Added by test'

    # Verify Doc 2 changes
    saved_doc2 = [d for d in saved_corpus if d.get_block('Paragraphs').get_text() == 'Modified: Only 1 paragraph here'][0]
    assert saved_doc2.get_block('Paragraphs').get_text() == 'Modified: Only 1 paragraph here'

    list_block2 = saved_doc2.get_list_block('List Block')
    assert len(list_block2) == 2  # Original named item + new unnamed item
    assert list_block2[1].get_name() is None
    assert list_block2[1].get_text() == "Why, hello there! I'm a new addition to this family."
