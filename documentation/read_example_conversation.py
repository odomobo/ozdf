"""
Example script showing how to read and display a conversation from an OZDF file.
"""

import ozdf


def main():
    # Open the example conversation document
    doc = ozdf.open_document('example conversation.ozdf')

    # Get the conversation list block
    conversation = doc.get_list_block('Conversation')

    # Iterate over each conversation item and print
    for item in conversation:
        user = item.get_name()
        text = item.get_text()
        print(f"{user}: {text}")


if __name__ == '__main__':
    main()
