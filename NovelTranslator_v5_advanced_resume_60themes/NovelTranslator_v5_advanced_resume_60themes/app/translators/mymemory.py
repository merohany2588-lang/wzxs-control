from __future__ import annotations

from .base import BaseTranslator, TranslatorError
from .lang import normalize_lang


class MyMemoryTranslatorEngine(BaseTranslator):
    engine_id = "mymemory"
    engine_name = "MyMemory 免费"

    def translate(self, text: str, source: str = "zh", target: str = "en") -> str:
        try:
            from deep_translator import MyMemoryTranslator
            source = normalize_lang(self.engine_id, source, "source")
            target = normalize_lang(self.engine_id, target, "target")
            result = MyMemoryTranslator(source=source, target=target).translate(text)
            if not result or not result.strip():
                raise TranslatorError("MyMemory 返回空结果")
            return result
        except Exception as e:
            raise TranslatorError(f"MyMemory 翻译失败：{e}") from e
