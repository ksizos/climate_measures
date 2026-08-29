from __future__ import annotations

from infrastructure.llm.provider import (
    chat_text,
)

from prompts.dialog import (
    DIALOG_SYSTEM_PROMPT,
)


def generate_dialog_response(
    user_question: str,
    conversation_history: str | None = None,
) -> str:

    history_block = ""

    if conversation_history:
        history_block = f"""
История диалога:
{conversation_history}
""".strip()

    user_prompt = f"""
{history_block}

Запрос пользователя:
{user_question}
""".strip()

    return chat_text(
        system_prompt=DIALOG_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.4,
        max_new_tokens=2000,
    )