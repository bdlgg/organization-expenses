from documents import (
    Document,
    add_document,
    find_document
)


def test_find_document():
    documents = []

    document = Document("Счет №101")

    add_document(
        documents,
        document
    )

    result = find_document(
        documents,
        "счет №101"
    )

    assert result is document