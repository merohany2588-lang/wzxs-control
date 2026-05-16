from __future__ import annotations

import time
from typing import Callable

from .base import BaseTranslator, TranslatorError
from .tencent import TencentTranslator
from .baidu import BaiduTranslator
from .google_free import GoogleFreeTranslator
from .mymemory import MyMemoryTranslatorEngine
from .libre import LibreTranslator
from .opus_mt import OpusMTTranslator


LogFunc = Callable[[str, str], None]


STRATEGY_ORDERS = {
    "free_first": ["google_free", "mymemory", "libre", "opus_mt"],
    "stable_api": ["tencent", "baidu", "google_free", "opus_mt", "mymemory"],
    "api_offline": ["tencent", "baidu", "opus_mt", "google_free", "mymemory"],
    "free_offline": ["google_free", "mymemory", "opus_mt", "tencent", "baidu"],
    "free_api_offline": ["google_free", "mymemory", "tencent", "baidu", "opus_mt"],
    "offline_first": ["opus_mt", "google_free", "mymemory"],
    "tencent_first": ["tencent", "baidu", "opus_mt", "google_free", "mymemory"],
    "baidu_first": ["baidu", "tencent", "opus_mt", "google_free", "mymemory"],
    "custom": None,
}


class TranslateEngineManager:
    def __init__(self, cfg: dict, log_func: LogFunc | None = None):
        self.cfg = cfg
        self.log_func = log_func
        self.retries = int(cfg.get("retry_times", 3))
        self.interval = float(cfg.get("request_interval", 0.8))
        self.strategy = cfg.get("strategy", "stable_api")
        self.engines = self._build_engines()

    def log(self, msg: str, level: str = "info") -> None:
        if self.log_func:
            self.log_func(msg, level)

    def _build_all_enabled_engines(self) -> dict[str, BaseTranslator]:
        cfg = self.cfg
        engines_map: dict[str, BaseTranslator] = {}

        t = cfg.get("tencent", {})
        if t.get("enabled"):
            engines_map["tencent"] = TencentTranslator(
                t.get("secret_id", ""),
                t.get("secret_key", ""),
                t.get("region", "ap-guangzhou"),
            )

        b = cfg.get("baidu", {})
        if b.get("enabled"):
            engines_map["baidu"] = BaiduTranslator(
                b.get("app_id", ""),
                b.get("secret_key", ""),
            )

        g = cfg.get("google_free", {})
        if g.get("enabled"):
            engines_map["google_free"] = GoogleFreeTranslator()

        m = cfg.get("mymemory", {})
        if m.get("enabled"):
            engines_map["mymemory"] = MyMemoryTranslatorEngine()

        l = cfg.get("libre", {})
        if l.get("enabled"):
            engines_map["libre"] = LibreTranslator(
                l.get("api_url", ""),
                l.get("api_key", ""),
            )

        o = cfg.get("opus_mt", {})
        if o.get("enabled"):
            engines_map["opus_mt"] = OpusMTTranslator(
                o.get("model_path", ""),
                o.get("device", "auto"),
                o.get("max_new_tokens", 900),
                o.get("offline_only", False),
            )

        return engines_map

    def _resolve_order(self) -> list[str]:
        if self.strategy in STRATEGY_ORDERS and STRATEGY_ORDERS[self.strategy] is not None:
            return list(STRATEGY_ORDERS[self.strategy])
        return list(self.cfg.get("engine_order", ["tencent", "baidu", "google_free", "opus_mt", "mymemory"]))

    def _build_engines(self) -> list[BaseTranslator]:
        engines_map = self._build_all_enabled_engines()
        order = self._resolve_order()

        engines: list[BaseTranslator] = []
        used = set()
        for key in order:
            if key in engines_map and key not in used:
                engines.append(engines_map[key])
                used.add(key)

        # 自定义顺序遗漏的已启用引擎，放最后
        for key, engine in engines_map.items():
            if key not in used:
                engines.append(engine)

        if not engines:
            engines = [GoogleFreeTranslator()]

        return engines

    def available_engine_names(self) -> list[str]:
        return [e.engine_name for e in self.engines]

    def translate(self, text: str, source: str = "zh", target: str = "en") -> tuple[str, str]:
        errors = []

        for engine in self.engines:
            for attempt in range(1, self.retries + 1):
                try:
                    self.log(f"策略：{self.strategy}；当前引擎：{engine.engine_name}；第 {attempt} 次尝试", "engine")
                    result = engine.translate(text, source=source, target=target)
                    result = result.strip()
                    if not result:
                        raise TranslatorError("返回空结果")
                    return result, engine.engine_name
                except Exception as e:
                    msg = f"{engine.engine_name} 第 {attempt} 次失败：{e}"
                    errors.append(msg)
                    self.log(msg, "warning")
                    time.sleep(self.interval * attempt)

            self.log(f"切换下一个引擎：{engine.engine_name} 已跳过", "switch")

        raise TranslatorError("所有翻译引擎均失败：\n" + "\n".join(errors))
