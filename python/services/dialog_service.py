from infrastructure.llm.providers.provider_registry import (
    call_dialog_service_text
)
from prompts.dialog import DIALOG_SYSTEM_PROMPT

def generate_dialog_response(
    user_question: str,
    conversation_history: str | None = None,
) -> str:
    history_instruction = ""

    if conversation_history:
        history_instruction = (
            "\n\nИстория диалога:\n"
            f"{conversation_history}\n\n"
            "Учитывай предыдущие сообщения."
        )

    full_prompt = (
        f"{history_instruction}\n\n"
        f"Запрос пользователя: {user_question}"
    ).strip()

    return call_dialog_service_text(
        user_prompt=full_prompt,
        system_prompt=DIALOG_SYSTEM_PROMPT,
        temperature=0.5,
        max_output_tokens=2500,
    )
