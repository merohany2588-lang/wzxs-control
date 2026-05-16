from __future__ import annotations

from pathlib import Path

from .base import BaseTranslator, TranslatorError
from .lang import normalize_lang


class OpusMTTranslator(BaseTranslator):
    engine_id = "opus_mt"
    engine_name = "OPUS-MT 本地"

    def __init__(
        self,
        model_path: str,
        device: str = "auto",
        max_new_tokens: int = 900,
        offline_only: bool = False,
    ):
        self.model_path = model_path
        self.device = device
        self.max_new_tokens = int(max_new_tokens or 900)
        self.offline_only = bool(offline_only)
        self._tokenizer = None
        self._model = None
        self._torch_device = None

    def _ensure_model(self):
        if self._model is not None and self._tokenizer is not None:
            return self._tokenizer, self._model, self._torch_device

        if not self.model_path:
            raise TranslatorError("OPUS-MT 模型路径未配置")

        model_path = Path(self.model_path)
        if not model_path.exists():
            raise TranslatorError(f"OPUS-MT 模型路径不存在：{model_path}")

        try:
            import os
            if self.offline_only:
                os.environ["TRANSFORMERS_OFFLINE"] = "1"
                os.environ["HF_HUB_OFFLINE"] = "1"

            import torch
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

            if self.device == "cuda":
                torch_device = "cuda"
            elif self.device == "cpu":
                torch_device = "cpu"
            else:
                torch_device = "cuda" if torch.cuda.is_available() else "cpu"

            tokenizer = AutoTokenizer.from_pretrained(str(model_path), local_files_only=self.offline_only)
            model = AutoModelForSeq2SeqLM.from_pretrained(str(model_path), local_files_only=self.offline_only)
            model.to(torch_device)
            model.eval()

            self._tokenizer = tokenizer
            self._model = model
            self._torch_device = torch_device
            return tokenizer, model, torch_device
        except Exception as e:
            raise TranslatorError(f"OPUS-MT 初始化失败：{e}") from e

    def translate(self, text: str, source: str = "zh", target: str = "en") -> str:
        try:
            import torch
            tokenizer, model, torch_device = self._ensure_model()

            # Marian OPUS-MT normally accepts plain source text; model path determines direction.
            source = normalize_lang(self.engine_id, source, "source")
            target = normalize_lang(self.engine_id, target, "target")

            inputs = tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True,
            )
            inputs = {k: v.to(torch_device) for k, v in inputs.items()}

            with torch.no_grad():
                generated = model.generate(
                    **inputs,
                    max_new_tokens=self.max_new_tokens,
                    num_beams=4,
                    early_stopping=True,
                )

            out = tokenizer.batch_decode(generated, skip_special_tokens=True)[0].strip()
            if not out:
                raise TranslatorError("OPUS-MT 返回空结果")
            return out
        except Exception as e:
            if isinstance(e, TranslatorError):
                raise
            raise TranslatorError(f"OPUS-MT 翻译失败：{e}") from e
