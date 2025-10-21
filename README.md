# Ozone Data Format

*The air was thick with metallic dust and the faint scent of ozone.*

The Ozone Data Format (ozdf) is a data format designed for managing small-to-medium datasets for finetuning LLMs *on prose*. It's quite opinionated, and has some limitations which make it very specific-purpose. If you need more flexibility, consider using jsonl like the rest of the world (or maybe check out toml).

The basic unit in Ozone Data Format is the "document". A document may either be a standalone file (.ozdf), or a directory containing a `_metadata.ozdf` file. Documents are contained in a "corpus", which refers to the directory that contains 1 or more documents. Documents themselves contain "block"s. There are no more levels - you can't store documents in documents, or any nonsense like that. Just corpus -> document -> block (well, kinda...). Instead of droning on and on, let me just show you what a typical document looks like:

```
#### TITLE
Little Women

#### AUTHOR
Louisa May Alcott

#### [BOOK CHAPTERS]
==== PLAYING PILGRIMS
"Christmas won't be Christmas without any presents," grumbled Jo, lying
on the rug.

"It's so dreadful to be poor!" sighed Meg, looking down at her old
dress.

"I don't think it's fair for some girls to have plenty of pretty
things, and other girls nothing at all," added little Amy, with an
injured sniff.

...

and it had become a household custom, for the mother was a born singer.
The first sound in the morning was her voice as she went about the
house singing like a lark, and the last sound at night was the same
cheery sound, for the girls never grew too old for that familiar
lullaby.

==== A MERRY CHRISTMAS
Jo was the first to wake in the gray dawn of Christmas morning. No
stockings hung at the fireplace, and for a moment she felt as much
disappointed as she did long ago, when her little sock fell down
because it was crammed so full of goodies. ...
```

One thing to note about block names is that they are always uppercase. If you don't make them uppercase, they will be treated (and saved) as uppercase.

As you can see, there are 2 types of blocks: standard blocks, and list blocks (in [square brackets] ). I hear you grumbling how there's another level of depth - of something deeper than a block. Ok, ok, you caught me - list blocks contain list items (which optionally can be named), and list items contain 1 or more paragraphs. As you can't see, normal blocks also can contain 1 or more paragraphs. I guess the paragraph is another layer of depth. So, to be precise, here's the structure of an ozone corpus:

```
corpus -> document -> block -> paragraph
-or-
corpus -> document -> block -> list block -> list item -> paragraph
```

Paragraphs are always normalized before being processed no matter whether they are in standard blocks or list items. "Normalized" means extra whitespace and newlines get stripped out. This is basically how paragraphs in html work. Whitespace is just ignored.

This is great if you're *only* interested in prose. Which I am! But if you want something that gives you more control over formatting, then you'll need another format.

## External List Blocks

But wait - there's more! Remember how I mentioned directory documents? Well, they have a `_metadata.ozdf file` that looks a lot like the documents I showed above, but they have one additional block type - the "external list block". External list blocks act like normal list blocks, but they don't directly contain their own data. Instead, they reference a series of "ozone data part" files. Here, see the example from above, but now using a directory document with an external list (note the [[double square brackets]] ):

_metadata.ozdf:

```
#### TITLE
Little Women

#### AUTHOR
Louisa May Alcott

#### [[BOOK CHAPTERS]]
```

BOOK_CHAPTERS-01.ozdp:

```
#### NAME
PLAYING PILGRIMS

#### DATA
"Christmas won't be Christmas without any presents," grumbled Jo, lying
on the rug.

...
```

BOOK_CHAPTERS-02.ozdp:

```
#### NAME
A MERRY CHRISTMAS

#### DATA
Jo was the first to wake in the gray dawn of Christmas morning. ...
```

There are a few special things to note:

Spaces in the external list block name are replaced with underscores. The ozdp files have to match that exactly. Basically, all ozdp files have to match: `{EXTERNAL_LIST_BLOCK_NAME}-{index}.ozdp` . Note that index has to start at 1 (or 01 or 001... you get the idea).

The "NAME" block in a data part file is optional, and references the list item name. The "DATA" block is mandatory, and contains the data for that particular list item.

Hopefully this is all clear just from looking at the examples.

## Comments

ozdf files can also contain comments. A comment is just a normal block with the name "COMMENT". An ozdf file can have multiple comments, even though normally block names need to be distinct.

# Ozone Data Format python library

Ok, now that you understand the data format, witness the ozdf python library! It's designed to be simple and straightforward. Behold:

```python
import ozdf

corpus = ozdf.open_corpus_readonly('path/to/corpus')
for document in corpus:
    title_block = document.get_block("Title") # case-insensitive, but the block name is actually "TITLE"
    print(f'# {title_block.get_text()}\n')

    for i, list_item in enumerate(document.get_list_block("Content")):
        print(f'## Chapter {i+1}')
        for paragraph in list_item:
            print(f'{paragraph}\n\n')
```

Note that you generally want all documents in a corpus to have the same structure, so you can process them all similarly. Also note that it doesn't matter for a particular document whether its "CONTENT" list block is a normal list block, or if it's an external list block. They're processed just the same.

Note that you can open corpuses (ok, "corpora", but English is silly) as read-write (or even write-only). See here how you'd do that. Note that when you open for writing, it will never write in place, but will write to a different output directory. If you make a mistake, the library will never mess up your input data.

```python
import ozdf

with ozdf.open_corpus_readwrite('path/to/input', 'path/to/output') as corpus:
    for document in [d for d in corpus if d.get_block("GENRE").get_text() == "Action"]:
        for item in document.get_list_block("CHAPTERS"):
            for i, paragraph in enumerate(item):
                item[i] = paragraph + " WOW!"

# changes to the new corpus are saved when it goes out of scope, but you can also save manually with corpus.save
```

You can basically manipulate blocks and list items in terms of either their paragraphs, or as their "text", which is all the paragraphs combined with a blank line between each.

You can add and remove blocks, list blocks, and external list blocks on documents and directory documents (although plain document files don't support external list blocks).

Take a look at `ozdf_cheatsheet.txt` to see the full functionality.

## Installation

Install from source:

```bash
git clone https://github.com/odomobo/ozdf
cd ozdf
pip install -e .
```

Someday maybe you'll be able to install it like this:

```bash
pip install ozdf
```
