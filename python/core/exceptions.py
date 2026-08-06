class ApplicationError(Exception):
    """
    Базовое исключение приложения.

    Используется для ожидаемых ошибок бизнес-логики,
    которые не относятся напрямую к HTTP.
    """

    default_message = "Ошибка приложения"

    def __init__(
        self,
        message: str | None = None,
    ) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class ValidationError(ApplicationError):
    """
    Ошибка проверки входных или сгенерированных данных.
    """

    default_message = "Некорректные данные"


class DatabaseError(ApplicationError):
    """
    Ошибка выполнения операции с базой данных.
    """

    default_message = "Ошибка базы данных"


class IndexRebuildError(ApplicationError):
    """
    Ошибка перестроения поискового или векторного индекса.
    """

    default_message = "Ошибка перестроения индекса"


class LLMResponseError(ApplicationError):
    """
    Ошибка вызова LLM или обработки ответа модели.
    """

    default_message = "Ошибка обработки ответа языковой модели"


class StructuredDataError(LLMResponseError):
    """
    Ошибка генерации или разбора структурированных данных.
    """

    default_message = "Не удалось сформировать структурированные данные"
