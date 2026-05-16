from __future__ import annotations

import re


def split_text_by_chars(text: str, max_chars: int = 1800) -> list[str]:
    """
    小说长文本分段：
    1. 优先按空行/段落切
    2. 超长段落再按中文标点切
    3. 仍然超长时硬切
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    raw_parts = [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]

    sentence_parts: list[str] = []
    for part in raw_parts:
        if len(part) <= max_chars:
            sentence_parts.append(part)
            continue

        sentences = re.split(r"(?<=[。！？!?；;])", part)
        buf = ""
        for s in sentences:
            s = s.strip()
            if not s:
                continue
            if len(buf) + len(s) + 1 <= max_chars:
                buf += ("\n" if buf else "") + s
            else:
                if buf:
                    sentence_parts.append(buf)
                if len(s) <= max_chars:
                    buf = s
                else:
                    for i in range(0, len(s), max_chars):
                        sentence_parts.append(s[i:i+max_chars])
                    buf = ""
        if buf:
            sentence_parts.append(buf)

    final_parts: list[str] = []
    buf = ""
    for p in sentence_parts:
        if len(buf) + len(p) + 2 <= max_chars:
            buf += ("\n\n" if buf else "") + p
        else:
            if buf:
                final_parts.append(buf)
            buf = p
    if buf:
        final_parts.append(buf)

    return final_parts
