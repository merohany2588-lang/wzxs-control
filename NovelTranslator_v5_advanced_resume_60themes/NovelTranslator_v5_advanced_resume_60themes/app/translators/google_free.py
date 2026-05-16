from __future__ import annotations

from .base import BaseTranslator, TranslatorError
from .lang import normalize_lang


class GoogleFreeTranslator(BaseTranslator):
    engine_id = "google_free"
    engine_name = "Google 免费"

    def translate(self, text: str, source: str = "zh", target: str = "en") -> str:
        try:
            from deep_translator import GoogleTranslator
            source = normalize_lang(self.engine_id, source, "source")
            target = normalize_lang(self.engine_id, target, "target")
            result = GoogleTranslator(source=source, target=target).translate(text)
            if not result or not result.strip():
                raise TranslatorError("Google 免费返回空结果")
            return result
        except Exception as e:
            raise TranslatorError(f"Google 免费翻译失败：{e}") from e
