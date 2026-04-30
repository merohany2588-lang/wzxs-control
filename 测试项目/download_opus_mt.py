from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

BASE = Path(r"G:\AI_Models\translation")

models = {
    "opus-mt-en-zh": "Helsinki-NLP/opus-mt-en-zh",
    "opus-mt-zh-en": "Helsinki-NLP/opus-mt-zh-en",
}

for folder, model_id in models.items():
    save_dir = BASE / folder
    print("=" * 80)
    print("Downloading:", model_id)
    print("Save to:", save_dir)

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_id)

    tokenizer.save_pretrained(save_dir)
    model.save_pretrained(save_dir)

    print("OK:", save_dir)

print("All OPUS-MT models downloaded.")