# OZDF Python Library - Developer Guide

## Project Overview

This is a Python library for reading, writing, and manipulating OZDF (Ozone Data Format) files. OZDF is a human-readable format designed for storing unprocessed or partially-processed data for fine-tuning LLMs.

**Key Goals:**
- Easy to create and read
- Unambiguous to parse
- Easy to programmatically create
- All features necessary for processing training data

See `documentation/specification.txt` for the full format specification.

## Architecture Overview

The data model follows a strict hierarchy:

```
Corpus (collection of documents)
  + Document (contains blocks, list blocks, and comments)
    + Block (simple text with paragraphs)
      + Paragraphs (strings)
    + ListBlock (contains list items)
      + ListItem (contains paragraphs)
        + Paragraphs (strings)
    + Comment (raw text, no normalization)
```

**The 6 Core Classes:**
1. `Corpus` - Collection of documents, acts as context manager
2. `Document` - Contains blocks, list blocks, and comments
3. `Block` - Simple text block with one or more paragraphs
4. `ListBlock` - Contains one or more list items
5. `ListItem` - Contains paragraphs, supports indexing (inherits from Block)
6. `Comment` - Raw text block with no normalization

**Key Design Principle:** Eager loading - the entire corpus/document is loaded into memory immediately when opened.

## Module Responsibilities

- **models.py** - Core data structures (Corpus, Document, Block, ListBlock, ListItem, Comment). Each class has a `_serialize_to()` method (or `_save_to()` for Document) for writing itself to a file.
- **parser.py** - Parse .ozdf files, _metadata.ozdf files, and .ozdp data part files
- **normalization.py** - Text normalization (whitespace collapsing, paragraph handling)
- **io.py** - Entry points (open_corpus_readonly, open_corpus_readwrite, open_document)

## Key Design Decisions

1. **No lazy loading** - Everything is loaded into memory immediately when opened
2. **Single Corpus class** - Not separate read-only/read-write classes. The Corpus has an optional `save_path`. If `save_path` is `None`, calling `save()` raises a RuntimeError
3. **Case-insensitive block lookups** - Block and list block names are stored in uppercase internally
4. **Dirty tracking** - Only modified documents are written on save. Block, ListItem, and ListBlock all maintain parent references to their Document for dirty tracking.
5. **Text normalization on set** - Normalization (whitespace collapsing, paragraph formatting) happens when `set_text()` is called on Block or ListItem. Normalization is also applied during serialization as a safety measure. Comments are never normalized.
6. **Corpus is a context manager** - Use `with` statement for auto-save on exit
7. **Parent references are mandatory** - Block, ListItem, and ListBlock require a parent Document reference for dirty tracking
8. **Document order tracking** - Document maintains `_ordered_elements` list to preserve the order of all elements (blocks, list blocks, comments)
9. **Error messages include filename** - All errors raised by Document include the filename to help identify issues in large corpora
10. **Serialization methods are private** - `_serialize_to()` and `_save_to()` are internal implementation details

## File Format Notes

### Simple Documents
- Single `.ozdf` file
- Contains blocks (`#### BlockName`) and list blocks (`#### [ListName]`)
- List items marked with `==== ItemName` or `====`

### Directory Documents
- Directory containing:
  - `_metadata.ozdf` - Contains document structure with external list blocks marked as `#### [[Name]]`
  - Multiple `.ozdp` files - Per-list-block data files named `{LIST_BLOCK_NAME}-{INDEX}.ozdp`
- Each external list block has its own series of `.ozdp` files (e.g., `MESSAGES-01.ozdp`, `MESSAGES-02.ozdp`)
- `.ozdp` files contain `#### NAME` (optional) and `#### DATA` (required) blocks
- Indexes start at 1 and must be contiguous (no gaps)
- Different external list blocks can have different numbers of items

### Comment Blocks
- `#### Comment` blocks are parsed and preserved in the document
- Comments store raw text without any normalization
- Comments are maintained in document order via `_ordered_elements`

### Validation Rules
- No line can start with `###` or `===` unless it's a header
- Indexes in .ozdp files must be sequential starting from 1
- Block names must be unique within a document

## Development Guidelines

### Development Approach

**We are following an incremental, test-driven approach:**

- Implement one part of the codebase at a time
- Write tests first, then implement the code to make them pass
- If you ever think about doing an extensive change that touches many parts of the codebase at once, **STOP** - this is probably a sign you're doing something wrong
- Step back and reconsider what is being asked
- Focus on small, isolated changes that build on each other

### Running Tests
```bash
cd tests
python test_basic.py
```

### Code Organization
- All parsing logic goes in `parser.py`
- Serialization is handled by `_serialize_to()` methods on model classes in `models.py`
- Models contain data structures plus serialization logic
- Keep I/O operations in `io.py`

### Patterns to Follow
- Use type hints throughout
- Raise clear exceptions with helpful messages
- Document all public methods with docstrings
- Keep functions focused and single-purpose
- **All imports must be at the top of the file** - never use inline imports within functions or methods

## Named Activities

### Creating a Checkpoint

When the user asks you to "create a checkpoint", you should create a new `CHECKPOINT.md` file in the project root. The purpose of a checkpoint is to capture the current state of work so that development can be paused at any time and easily resumed later, even in a fresh Claude Code session.

**Structure Guidelines:**

A checkpoint should include these **required sections**:

1. **What We're Working On** - Brief description of the current task/feature/bug
2. **Current State** - Where things stand right now (working? broken? partially implemented?)
3. **Next Steps** - Numbered list of specific actions to take next

And these **optional sections** as needed:

4. **Important Background** - Key architectural decisions, discoveries, or non-obvious gotchas that would be hard to reconstruct
5. **Blockers** - Anything that's blocking progress or needs discussion
6. **Active Work Context** - Files being actively worked on, specific code locations, or other context needed to understand the current work

**Guidelines for Writing Checkpoints:**

- Be specific in "Next Steps" - someone should be able to start immediately
- Refer to specifics in the code where applicable (e.g., file paths, function names, line numbers)
- Focus on what matters - don't document everything, just what's needed to resume effectively

### Go Next Step

When the user asks you to "go next step", you should implement **only the next uncompleted step** from the current implementation plan.

**Prerequisites:**

- There must be a current implementation plan file
- If no clear implementation plan exists, inform the user that "go next step" is invalid without a plan

**Process:**

1. **Read the implementation plan** - Find the plan file and identify the next uncompleted step (first item with `[ ]`)
2. **Verify it's a single step** - Ensure you're implementing exactly ONE checkbox item, not a whole phase
3. **Implement the step** - Write code, update tests, or make the required changes for that specific step only
4. **Test the change** - Run relevant tests to verify the step works correctly
5. **Mark step complete** - Update the plan file by changing `[ ]` to `[x]` for the completed step
6. **Report completion** - Tell the user what step was completed and what the next step will be

**Important Guidelines:**

- **One step at a time** - Never implement multiple steps in a single "go next step" invocation
- **Follow the plan exactly** - Don't skip steps or reorder them unless you identify an issue with the plan itself
- **Update the plan** - Always mark the step as complete in the plan file
- **Be incremental** - The whole point is to make small, verifiable progress step by step

**Example:**

```
User: "go next step"
