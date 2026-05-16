from __future__ import annotations

import json
import os
import platform
import subprocess
from pathlib import Path
from datetime import datetime
from charset_normalizer import from_path


ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT_DIR / "config" / "translator_config.json"
OUTPUT_DIR = ROOT_DIR / "output"
LOG_DIR = ROOT_DIR / "logs"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"配置文件不存在：{CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def read_text_auto(path: str | Path) -> str:
    path = Path(path)
    result = from_path(str(path)).best()
    if result is None:
        for enc in ("utf-8-sig", "utf-8", "gb18030", "gbk", "big5"):
            try:
                return path.read_text(encoding=enc)
            except Exception:
                pass
        raise UnicodeDecodeError("unknown", b"", 0, 1, "无法识别文本编码")
    return str(result)


def safe_filename(name: str) -> str:
    invalid = '<>:"/\\|?*'
    for ch in invalid:
        name = name.replace(ch, "_")
    return name.strip() or "output"


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def fmt_time(seconds: float) -> str:
    seconds = int(max(0, seconds))
    h = seconds // 3600
    m = seconds % 3600 // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def open_dir(path: str | Path) -> None:
    path = str(Path(path).resolve())
    system = platform.system()
    if system == "Windows":
        os.startfile(path)  # type: ignore[attr-defined]
    elif system == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])
