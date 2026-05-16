from __future__ import annotations

import hashlib
import random
import requests

from .base import BaseTranslator, TranslatorError
from .lang import normalize_lang


class BaiduTranslator(BaseTranslator):
    engine_id = "baidu"
    engine_name = "百度翻译"

    def __init__(self, app_id: str, secret_key: str):
        self.app_id = app_id
        self.secret_key = secret_key
        self.api_url = "https://fanyi-api.baidu.com/api/trans/vip/translate"

    def _sign(self, text: str, salt: int) -> str:
        raw = self.app_id + text + str(salt) + self.secret_key
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def translate(self, text: str, source: str = "zh", target: str = "en") -> str:
        if not self.app_id or not self.secret_key:
            raise TranslatorError("百度 APP ID 或 SecretKey 未配置")

        source = normalize_lang(self.engine_id, source, "source")
        target = normalize_lang(self.engine_id, target, "target")
        salt = random.randint(32768, 65536)
        params = {
            "q": text,
            "from": source,
            "to": target,
            "appid": self.app_id,
            "salt": salt,
            "sign": self._sign(text, salt),
        }

        try:
            r = requests.get(self.api_url, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            raise TranslatorError(f"百度请求失败：{e}") from e

        if "error_code" in data:
            raise TranslatorError(f"百度返回错误：{data}")

        if "trans_result" not in data:
            raise TranslatorError(f"百度返回格式异常：{data}")

        result = "\n".join(item.get("dst", "") for item in data["trans_result"]).strip()
        if not result:
            raise TranslatorError("百度返回空结果")
        return result
