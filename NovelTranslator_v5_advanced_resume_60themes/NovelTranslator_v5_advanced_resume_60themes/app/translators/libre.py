from __future__ import annotations

import requests

from .base import BaseTranslator, TranslatorError


class LibreTranslator(BaseTranslator):
    engine_id = "libre"
    engine_name = "LibreTranslate"

    def __init__(self, api_url: str, api_key: str = ""):
        self.api_url = api_url or "https://libretranslate.com/translate"
        self.api_key = api_key or ""

    def translate(self, text: str, source: str = "zh", target: str = "en") -> str:
        payload = {
            "q": text,
            "source": source,
            "target": target,
            "format": "text",
        }
        if self.api_key:
            payload["api_key"] = self.api_key

        try:
            r = requests.post(self.api_url, json=payload, timeout=40)
            r.raise_for_status()
            data = r.json()
            result = data.get("translatedText", "").strip()
        except Exception as e:
            raise TranslatorError(f"LibreTranslate 请求失败：{e}") from e

        if not result:
            raise TranslatorError(f"LibreTranslate 返回空结果：{data}")
        return result
