from __future__ import annotations

from abc import ABC, abstractmethod


class BaseTranslator(ABC):
    engine_id = "base"
    engine_name = "Base"

    @abstractmethod
    def translate(self, text: str, source: str = "zh", target: str = "en") -> str:
        raise NotImplementedError


class TranslatorError(RuntimeError):
    pass
