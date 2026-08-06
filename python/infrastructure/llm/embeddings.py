import os

from llama_index.core import Settings
from llama_index.embeddings.huggingface import (
    HuggingFaceEmbedding,
)
from core.config import EMBED_MODEL


embed_model = HuggingFaceEmbedding(
    model_name=EMBED_MODEL,
)

Settings.embed_model = embed_model
