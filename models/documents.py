from typing import List


class Document:
    """Документ, связанный с расходом."""

    def __init__(self, number: str) -> None:
        self.number = number

    def matches(self, query: str) -> bool:
        """Проверить совпадение номера документа с запросом."""
        return query.lower() in self.number.lower()

    def __str__(self) -> str:
        """Вернуть строковое представление документа."""
        return self.number

    @classmethod
    def from_data(cls, data: dict) -> "Document":
        """Создать объект Document из данных JSON."""
        return cls(number=data["number"])


def add_document(
    documents: List[Document],
    number: str,
) -> None:
    """Добавить документ в коллекцию."""
    documents.append(Document(number))


def find_document(
    documents: List[Document],
    query: str,
) -> List[Document]:
    """Найти документы по номеру."""
    return [
        document
        for document in documents
        if document.matches(query)
    ]


def filter_documents(
    documents: List[Document],
    query: str,
) -> List[Document]:
    """Отфильтровать документы по номеру."""
    return find_document(documents, query)


def sort_documents(
    documents: List[Document],
) -> List[Document]:
    """Вернуть документы в порядке номеров."""
    return sorted(documents, key=lambda document: document.number)
