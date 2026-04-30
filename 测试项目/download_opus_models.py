from pathlib import Path
from huggingface_hub import snapshot_download

MODELS = {
    "Helsinki-NLP/opus-mt-en-zh": Path("models/opus-mt-en-zh"),
    "Helsinki-NLP/opus-mt-zh-en": Path("models/opus-mt-zh-en"),
}

for repo, out_dir in MODELS.items():
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {repo} -> {out_dir.resolve()}")
    snapshot_download(
        repo_id=repo,
        local_dir=str(out_dir),
        local_dir_use_symlinks=False,
        resume_download=True,
    )
print("OK: OPUS-MT models downloaded.")
