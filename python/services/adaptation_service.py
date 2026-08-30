from __future__ import annotations

import logging

from dataclasses import (
    dataclass,
    field,
)

from core.config import (
    ADAPTATION_TABLE,
)

from infrastructure.llm.provider import (
    chat_text,
)

from prompts.adaptation import (
    RAG_SYSTEM_PROMPT,
)

from services.vector_context_service import (
    RetrievedVectorDocument,
    retrieve_vector_context,
)


logger = logging.getLogger(
    __name__
)


ADAPTATION_REGISTRY_TOP_K = 4

ADAPTATION_CASE_TOP_K = 4


# =====================================================
# LOCAL ADAPTATION CONTEXT
# =====================================================

@dataclass(slots=True)
class AdaptationLocalContextResult:

    registry_documents: list[
        RetrievedVectorDocument
    ] = field(
        default_factory=list
    )

    case_documents: list[
        RetrievedVectorDocument
    ] = field(
        default_factory=list
    )

    @property
    def total_count(
        self,
    ) -> int:

        return (
            len(
                self.registry_documents
            )
            +
            len(
                self.case_documents
            )
        )

    def to_context(
        self,
    ) -> str:

        parts: list[str] = []

        # =====================================
        # EXPERT REGISTRY
        # =====================================

        parts.append(
            "=== ЭКСПЕРТНЫЙ РЕЕСТР "
            "АДАПТАЦИОННЫХ МЕРОПРИЯТИЙ ==="
        )

        if not self.registry_documents:

            parts.append(
                "Релевантные мероприятия "
                "в экспертном реестре "
                "не найдены."
            )

        else:

            for index, document in (
                enumerate(
                    self.registry_documents,
                    start=1,
                )
            ):

                metadata = (
                    document.metadata
                    or {}
                )

                block: list[str] = [
                    (
                        f"[ADAPT-REGISTRY-"
                        f"{index}]"
                    )
                ]

                block.append(
                    document.text
                )

                funding_source = str(
                    metadata.get(
                        "funding_source",
                        "",
                    )
                ).strip()

                if funding_source:
                    block.append(
                        "Источник финансирования: "
                        f"{funding_source}"
                    )

                source_reference = str(
                    metadata.get(
                        "source_reference",
                        "",
                    )
                ).strip()

                if source_reference:
                    block.append(
                        "Источник / основание: "
                        f"{source_reference}"
                    )

                if (
                    document.score
                    is not None
                ):
                    block.append(
                        "Релевантность: "
                        f"{document.score:.4f}"
                    )

                parts.append(
                    "\n".join(
                        block
                    )
                )

        # =====================================
        # CASES
        # =====================================

        parts.append(
            "=== ПРАКТИЧЕСКИЕ "
            "АДАПТАЦИОННЫЕ КЕЙСЫ ==="
        )

        if not self.case_documents:

            parts.append(
                "Релевантные практические "
                "кейсы не найдены."
            )

        else:

            for index, document in (
                enumerate(
                    self.case_documents,
                    start=1,
                )
            ):

                metadata = (
                    document.metadata
                    or {}
                )

                block: list[str] = [
                    (
                        f"[ADAPT-CASE-"
                        f"{index}]"
                    )
                ]

                title = str(
                    metadata.get(
                        "title",
                        "",
                    )
                ).strip()

                if title:
                    block.append(
                        "Мероприятие кейса: "
                        f"{title}"
                    )

                district = str(
                    metadata.get(
                        "district",
                        "",
                    )
                ).strip()

                if district:
                    block.append(
                        "Территория кейса: "
                        f"{district}"
                    )

                climate_conditions = str(
                    metadata.get(
                        "climate_conditions",
                        "",
                    )
                ).strip()

                if climate_conditions:
                    block.append(
                        "Климатические условия: "
                        f"{climate_conditions}"
                    )

                responsible_org = str(
                    metadata.get(
                        "responsible_org",
                        "",
                    )
                ).strip()

                if responsible_org:
                    block.append(
                        "Организация "
                        "в исходном кейсе: "
                        f"{responsible_org}"
                    )

                url = str(
                    metadata.get(
                        "url",
                        "",
                    )
                ).strip()

                if url:
                    block.append(
                        f"URL: {url}"
                    )

                block.append(
                    "Содержание кейса:\n"
                    f"{document.text}"
                )

                if (
                    document.score
                    is not None
                ):
                    block.append(
                        "Релевантность: "
                        f"{document.score:.4f}"
                    )

                parts.append(
                    "\n".join(
                        block
                    )
                )

        return (
            "\n\n---\n\n"
            .join(parts)
        )


# =====================================================
# RETRIEVAL
# =====================================================

def retrieve_adaptation_local_context(
    query: str,
) -> AdaptationLocalContextResult:

    logger.info(
        "Adaptation local retrieval START: %s",
        query,
    )

    # -------------------------------------
    # Экспертный реестр
    # -------------------------------------

    registry_result = (
        retrieve_vector_context(
            query,
            table_name=(
                ADAPTATION_TABLE
            ),
            top_k=(
                ADAPTATION_REGISTRY_TOP_K
            ),
            metadata_filters={
                "source_type":
                    "registry",
            },
        )
    )

    # -------------------------------------
    # Практические кейсы
    # -------------------------------------

    case_result = (
        retrieve_vector_context(
            query,
            table_name=(
                ADAPTATION_TABLE
            ),
            top_k=(
                ADAPTATION_CASE_TOP_K
            ),
            metadata_filters={
                "source_type":
                    "case",
            },
        )
    )

    result = (
        AdaptationLocalContextResult(
            registry_documents=(
                registry_result.documents
            ),
            case_documents=(
                case_result.documents
            ),
        )
    )

    logger.info(
        "Adaptation local retrieval FINISHED: "
        "registry=%s, "
        "cases=%s",
        len(
            result.registry_documents
        ),
        len(
            result.case_documents
        ),
    )

    return result


# =====================================================
# ADAPTATION AGENT
# =====================================================

def generate_adaptation_response(
    user_question: str,
    conversation_history:
        str | None = None,
) -> str:

    logger.info(
        "Adaptation service START: %s",
        user_question,
    )

    local_result = (
        retrieve_adaptation_local_context(
            user_question
        )
    )

    history_block = ""

    if conversation_history:

        history_block = f"""
История диалога:
{conversation_history}
""".strip()

    local_context = (
        local_result.to_context()
    )

    user_prompt = f"""
{history_block}

Вопрос пользователя:
{user_question}

=== ЛОКАЛЬНАЯ БАЗА АДАПТАЦИОННЫХ МЕРОПРИЯТИЙ ===

{local_context}

Сформируй экспертный ответ
на вопрос пользователя.

Правила:

1. В локальном контексте есть
   два независимых типа источников:

   - экспертный реестр
     адаптационных мероприятий;

   - практические реализованные кейсы.

2. Экспертный реестр используй
   прежде всего для выбора
   обоснованных типов мероприятий,
   соответствующих климатическому риску.

3. Практические кейсы используй
   для:
   - подтверждения применимости мер;
   - уточнения практической реализации;
   - определения возможных
     адаптационных и митигационных эффектов;
   - сопоставления с климатическими
     и территориальными условиями.

4. Не считай,
   что мероприятие из кейса
   автоматически подходит пользователю.
   Оцени его применимость
   с учётом запроса.

5. Не считай,
   что мероприятие экспертного реестра
   обязательно должно иметь
   соответствующий практический кейс.

6. Допускается использовать
   одновременно экспертную меру
   и близкий практический кейс
   как два основания
   одной итоговой рекомендации.

7. Не приписывай экспертному реестру
   сведения, которые присутствуют
   только в практическом кейсе.

8. Не приписывай одному кейсу
   сведения из другого кейса.

9. Используй только мероприятия
   и факты,
   присутствующие в переданном контексте.

10. Учитывай:
    - климатический риск;
    - территорию;
    - отрасль;
    - климатические условия;
    - другие ограничения пользователя.

11. Сформируй 2–3
    наиболее релевантные рекомендации.

12. В основном тексте
    НИКОГДА не показывай
    технические метки:

    ADAPT-REGISTRY
    ADAPT-CASE

13. В разделе источников
    также никогда
    не показывай эти метки.

14. В конце ответа добавь:

### Источники

15. Перед формированием раздела источников
проверь каждую строку итоговой таблицы
и определи, какие элементы локального контекста
действительно были использованы
для создания этой строки.

В раздел "Источники" включай ТОЛЬКО те источники,
которые реально повлияли на содержание
итоговой таблицы.

Не включай источник только потому,
что он был найден векторным поиском
и присутствовал в контексте.

16. Если при формировании конкретной рекомендации
использовалось мероприятие из экспертного реестра,
укажи источник только как:

Реестр мероприятий

Не повторяй в разделе источников
название мероприятия из экспертного реестра.

Не выводи:
- название экспертного мероприятия;
- его measure_id;
- технические metadata;
- ADAPT-REGISTRY;
- название файла Excel.

17. Если две разные строки итоговой таблицы
были сформированы на основе экспертного реестра,
допускается указать "Реестр мероприятий"
отдельно для каждой такой строки.

Например:

1. Реестр мероприятий
2. Реестр мероприятий

18. Если при формировании рекомендации
реально использовался практический кейс,
укажи его в формате:

Название мероприятия или кейса. URL: точный_URL

Например:

3. Система очистки и отвода ливневых стоков
и талых вод с применением дренажных колодцев.
URL: https://example.ru/case

19. Практический кейс включай в источники
ТОЛЬКО если сведения из этого кейса
реально использованы при создании таблицы.

Если кейс был найден поиском,
но не использован в итоговых рекомендациях,
не включай его в источники.

20. Если одна рекомендация была сформирована
на основе экспертного реестра
и дополнительно уточнена практическим кейсом,
в разделе источников должны присутствовать
оба источника.

21. Нумеруй источники единым списком:

1. ...
2. ...
3. ...

Не создавай отдельные подразделы
"Экспертный реестр"
и "Практические кейсы".

22. Никогда не показывай пользователю
технические обозначения:

ADAPT-REGISTRY
ADAPT-CASE
measure_id
case_id
source_type

23. Для практических кейсов
копируй URL дословно из контекста.

Не изменяй URL и не придумывай ссылки.

24. Если у использованного практического кейса
URL отсутствует, укажи только его название.

25. Количество найденных RAG-документов
не определяет количество источников.
Источников должно быть столько,
сколько реально потребовалось
для формирования итогового ответа.
""".strip()

    answer = chat_text(
        system_prompt=(
            RAG_SYSTEM_PROMPT
        ),
        user_prompt=user_prompt,
        temperature=0.2,
        max_new_tokens=2800,
    )

    logger.info(
        "Adaptation service FINISHED: "
        "registry_documents=%s, "
        "case_documents=%s",
        len(
            local_result
            .registry_documents
        ),
        len(
            local_result
            .case_documents
        ),
    )

    return answer