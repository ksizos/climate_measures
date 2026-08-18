from transformers import AutoModelForCausalLM, AutoTokenizer


MODEL_NAME = "yandex/YandexGPT-5-Lite-8B-instruct"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map="cpu",
    torch_dtype="auto",
    low_cpu_mem_usage=True,
)

messages = [{"role": "user", "content": "Для чего нужна токенизация?"}]
input_ids = tokenizer.apply_chat_template(
    messages, tokenize=True, return_tensors="pt"
).to("cuda")

outputs = model.generate(input_ids, max_new_tokens=1024)
print(tokenizer.decode(outputs[0][input_ids.size(1) :], skip_special_tokens=True))