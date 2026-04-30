from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

MODEL_ID = "facebook/nllb-200-distilled-600M"
SAVE_DIR = Path(r"G:\AI_Models\translation\nllb-200-distilled-600M")

print("Downloading:", MODEL_ID)
print("Save to:", SAVE_DIR)

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_ID)

tokenizer.save_pretrained(SAVE_DIR)
model.save_pretrained(SAVE_DIR)

print("NLLB downloaded successfully.")