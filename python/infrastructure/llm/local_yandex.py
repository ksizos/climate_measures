from __future__ import annotations

import asyncio
from functools import lru_cache
import threading
from llama_index.core.llms import ChatMessage
from llama_index.llms.huggingface import HuggingFaceLLM
from transformers import AutoModelForCausalLM, AutoTokenizer

from core.config import (
    LOCAL_LLM_CONTEXT_WINDOW,
    LOCAL_LLM_DEVICE_MAP,
    LOCAL_LLM_MODEL_NAME,
    LOCAL_LLM_TOP_P,
)
_generation_lock = threading.Lock()


@lru_cache(maxsize=1)
def _load_model_bundle():
    tokenizer = AutoTokenizer.from_pretrained(
        LOCAL_LLM_MODEL_NAME,
    )

    model = AutoModelForCausalLM.from_pretrained(
        LOCAL_LLM_MODEL_NAME,
        device_map=LOCAL_LLM_DEVICE_MAP,
        torch_dtype="auto",
        low_cpu_mem_usage=True,
    )

    model.eval()

    return model, tokenizer


@lru_cache(maxsize=16)
def get_local_llm(
    temperature: float = 0.2,
    max_new_tokens: int = 2000,
) -> HuggingFaceLLM:

    model, tokenizer = _load_model_bundle()

    do_sample = temperature > 0

    generate_kwargs = {
        "do_sample": do_sample,
    }

    if do_sample:
        generate_kwargs.update(
            {
                "temperature": temperature,
                "top_p": LOCAL_LLM_TOP_P,
            }
        )

    return HuggingFaceLLM(
        model=model,
        tokenizer=tokenizer,
        model_name=LOCAL_LLM_MODEL_NAME,
        tokenizer_name=LOCAL_LLM_MODEL_NAME,
        context_window=LOCAL_LLM_CONTEXT_WINDOW,
        max_new_tokens=max_new_tokens,
        is_chat_model=True,
        query_wrapper_prompt="{query_str}",
        generate_kwargs=generate_kwargs,
    )


def chat_text(
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_new_tokens: int = 2000,
) -> str:

    llm = get_local_llm(
        temperature=temperature,
        max_new_tokens=max_new_tokens,
    )

    messages = [
        ChatMessage(
            role="system",
            content=system_prompt,
        ),
        ChatMessage(
            role="user",
            content=user_prompt,
        ),
    ]

    with _generation_lock:
        response = llm.chat(messages)

    return (
        response.message.content
        or ""
    ).strip()


async def achat_text(
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_new_tokens: int = 2000,
) -> str:

    return await asyncio.to_thread(
        chat_text,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=temperature,
        max_new_tokens=max_new_tokens,
    )


def preload_local_llm() -> None:
    _load_model_bundle()

def preload_llm() -> None:
    preload_local_llm()