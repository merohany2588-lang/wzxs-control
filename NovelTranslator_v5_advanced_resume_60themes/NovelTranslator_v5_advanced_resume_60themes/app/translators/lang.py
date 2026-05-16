from __future__ import annotations

def normalize_lang(engine: str, lang: str, role: str = "source") -> str:
    """
    Normalize UI language codes for different translation engines.
    UI uses: zh / zh-CN / en / ja / auto.
    """
    lang = (lang or "").strip()

    if engine in {"google_free", "mymemory"}:
        if lang in {"zh", "zh-cn", "zh_CN", "chinese", "中文"}:
            return "zh-CN"
        if lang in {"zh-tw", "zh_TW"}:
            return "zh-TW"
        if lang == "auto":
            return "auto"
        return lang

    if engine in {"baidu", "tencent"}:
        if lang in {"zh-CN", "zh-cn", "zh_CN", "chinese", "中文"}:
            return "zh"
        if lang in {"zh-TW", "zh-tw", "zh_TW"}:
            return "zh-TW"
        if lang == "auto":
            return "auto"
        return lang

    # OPUS local model path determines direction; source/target are mostly metadata.
    if lang in {"zh-CN", "zh-cn", "zh_CN"}:
        return "zh"
    return lang
