import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


MODEL_NAME = "yandex/YandexGPT-5-Lite-8B-instruct"

device = torch.device("cpu")

print(f"Используем устройство: {device}")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map="cpu",
    dtype="auto",
    low_cpu_mem_usage=True,
)

model.eval()

messages = [
    {
        "role": "user",
        "content": "расскажи про город Тюмень"
    }
]

input_ids = tokenizer.apply_chat_template(
    messages,
    tokenize=True,
    add_generation_prompt=True,
    return_tensors="pt",
).to(device)

with torch.inference_mode():
    outputs = model.generate(
        input_ids,
        max_new_tokens=128,
        do_sample=False,
    )

answer = tokenizer.decode(
    outputs[0][input_ids.size(1):],
    skip_special_tokens=True,
)

print("\nОТВЕТ:")
print(answer)