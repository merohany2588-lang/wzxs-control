from __future__ import annotations

import json

from .base import BaseTranslator, TranslatorError
from .lang import normalize_lang


class TencentTranslator(BaseTranslator):
    engine_id = "tencent"
    engine_name = "腾讯云翻译"

    def __init__(self, secret_id: str, secret_key: str, region: str = "ap-guangzhou"):
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.region = region or "ap-guangzhou"
        self._client = None

    def _ensure_client(self):
        if not self.secret_id or not self.secret_key:
            raise TranslatorError("腾讯云 SecretId 或 SecretKey 未配置")

        if self._client is not None:
            return self._client

        try:
            from tencentcloud.common import credential
            from tencentcloud.common.profile.client_profile import ClientProfile
            from tencentcloud.common.profile.http_profile import HttpProfile
            from tencentcloud.tmt.v20180321 import tmt_client

            cred = credential.Credential(self.secret_id, self.secret_key)
            http_profile = HttpProfile()
            http_profile.endpoint = "tmt.tencentcloudapi.com"
            client_profile = ClientProfile()
            client_profile.httpProfile = http_profile
            self._client = tmt_client.TmtClient(cred, self.region, client_profile)
            return self._client
        except Exception as e:
            raise TranslatorError(f"腾讯云 SDK 初始化失败：{e}") from e

    def translate(self, text: str, source: str = "zh", target: str = "en") -> str:
        try:
            from tencentcloud.tmt.v20180321 import models
            source = normalize_lang(self.engine_id, source, "source")
            target = normalize_lang(self.engine_id, target, "target")
            client = self._ensure_client()
            req = models.TextTranslateRequest()
            params = {
                "SourceText": text,
                "Source": source,
                "Target": target,
                "ProjectId": 0,
            }
            req.from_json_string(json.dumps(params, ensure_ascii=False))
            resp = client.TextTranslate(req)
            data = json.loads(resp.to_json_string())
            result = data.get("TargetText", "").strip()
            if not result:
                raise TranslatorError(f"腾讯云返回空结果：{data}")
            return result
        except Exception as e:
            if isinstance(e, TranslatorError):
                raise
            raise TranslatorError(f"腾讯云翻译失败：{e}") from e
