from typing import List, Optional


class Document:
    """Представляет документ, подтверждающий расход."""

    def __init__(self, number: str):
        self.number = number.strip()

    def matches(self, query: str) -> bool:
        """Проверить соответствие документа запросу."""

        return query.lower() in self.number.lower()

    def get_info(self) -> str:
        """Получить номер документа."""

        return self.number

    def to_dict(self) -> dict:
        """Преобразовать документ в словарь."""

        return {
            "number": self.number
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Document":
        """Создать документ из словаря."""

        return cls(data["number"])


def add_document(
    documents: List[Document],
    document: Document
) -> None:
    """Добавить документ, если его еще нет."""

    if find_document(documents, document.number) is None:
        documents.append(document)


def find_document(
    documents: List[Document],
    number: str
) -> Optional[Document]:
    """Найти документ по номеру."""

    for document in documents:
        if document.number.lower() == number.lower():
            return document

    return None


def filter_documents(
    documents: List[Document],
    query: str
) -> List[Document]:
    """Найти документы по подстроке."""

    return [
        document
        for document in documents
        if document.matches(query)
    ]


def sort_documents(
    documents: List[Document]
) -> List[Document]:
    """Отсортировать документы по номеру."""

    return sorted(
        documents,
        key=lambda document: document.number.lower()
    )