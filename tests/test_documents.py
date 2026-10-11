from models.documents import (
    Document,
    add_document,
    find_document,
    sort_documents,
)


def test_document_creation():
    document = Document("ДО-001")

    assert document.number == "ДО-001"


def test_document_str():
    document = Document("ДО-001")

    assert str(document) == "ДО-001"


def test_document_matches():
    document = Document("ДО-001")

    assert document.matches("001")
    assert not document.matches("002")


def test_add_document():
    documents = []

    add_document(documents, "ДО-001")

    assert len(documents) == 1
    assert documents[0].number == "ДО-001"


def test_find_document():
    documents = [
        Document("ДО-001"),
        Document("ДО-002"),
    ]

    result = find_document(documents, "001")

    assert len(result) == 1
    assert result[0].number == "ДО-001"


def test_sort_documents():
    documents = [
        Document("ДО-002"),
        Document("ДО-001"),
    ]

    result = sort_documents(documents)

    assert [document.number for document in result] == [
        "ДО-001",
        "ДО-002",
    ]