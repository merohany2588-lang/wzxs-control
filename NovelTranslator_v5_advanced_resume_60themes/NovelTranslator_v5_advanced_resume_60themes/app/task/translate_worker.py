from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import QThread, Signal

from app.splitter import split_text_by_chars
from app.translators.manager import TranslateEngineManager
from app.task.task_controller import TaskController
from app.utils import read_text_auto, safe_filename, now_stamp, fmt_time


class TranslateWorker(QThread):
    log_signal = Signal(str, str)
    progress_signal = Signal(int, int, float, float, float)
    finished_signal = Signal(str, str)
    failed_signal = Signal(str)

    def __init__(self, input_file: str, cfg: dict, source_lang: str, target_lang: str, parent=None):
        super().__init__(parent)
        self.input_file = input_file
        self.cfg = cfg
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.controller = TaskController()
        self.output_dir = ""

    def log(self, msg: str, level: str = "info") -> None:
        self.log_signal.emit(msg, level)

    def pause(self) -> None:
        self.controller.pause()
        self.log("用户暂停任务：当前段完成后暂停，已完成段落已经实时写入文件", "pause")

    def resume_task(self) -> None:
        self.controller.resume()
        self.log("用户继续任务", "resume")

    def cancel(self) -> None:
        self.controller.cancel()
        self.log("用户请求终止任务：当前段完成后停止，已完成内容已保存，可断点续译", "cancel")

    def _find_resume_dir(self, base_name: str) -> Path | None:
        if not self.cfg.get("resume_enabled", True):
            return None
        out_root = Path(__file__).resolve().parents[2] / "output"
        if not out_root.exists():
            return None

        candidates = []
        for d in out_root.glob(f"{base_name}_*"):
            cp = d / "checkpoint.json"
            if not cp.exists():
                continue
            try:
                data = json.loads(cp.read_text(encoding="utf-8"))
                if (
                    data.get("input_file") == str(Path(self.input_file))
                    and data.get("source_lang") == self.source_lang
                    and data.get("target_lang") == self.target_lang
                    and not data.get("completed", False)
                ):
                    candidates.append((d.stat().st_mtime, d))
            except Exception:
                pass
        if not candidates:
            return None
        candidates.sort(reverse=True)
        return candidates[0][1]

    def _write_checkpoint(
        self,
        checkpoint_file: Path,
        input_path: Path,
        done_indices: list[int],
        failed_parts: list[dict],
        total: int,
        completed: bool = False,
    ) -> None:
        data = {
            "input_file": str(input_path),
            "output_dir": str(checkpoint_file.parent),
            "source_lang": self.source_lang,
            "target_lang": self.target_lang,
            "total_chunks": total,
            "done_indices": done_indices,
            "failed_count": len(failed_parts),
            "failed_parts": failed_parts,
            "completed": completed,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        checkpoint_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def run(self) -> None:
        try:
            input_path = Path(self.input_file)
            if not input_path.exists():
                raise FileNotFoundError(f"文件不存在：{input_path}")

            base_name = safe_filename(input_path.stem)
            out_root = Path(__file__).resolve().parents[2] / "output"
            out_root.mkdir(parents=True, exist_ok=True)

            resume_dir = self._find_resume_dir(base_name)
            if resume_dir is not None:
                out_dir = resume_dir
                self.log(f"发现未完成任务，继续断点续译：{out_dir}", "resume")
            else:
                out_dir = out_root / f"{base_name}_{now_stamp()}"
                out_dir.mkdir(parents=True, exist_ok=True)

            self.output_dir = str(out_dir)
            checkpoint_file = out_dir / "checkpoint.json"

            self.log(f"读取文件：{input_path}", "info")
            text = read_text_auto(input_path)
            max_chars = int(self.cfg.get("max_chars_per_chunk", 1800))
            chunks = split_text_by_chars(text, max_chars=max_chars)
            if not chunks:
                raise RuntimeError("没有可翻译内容")

            translated_file = out_dir / f"{base_name}_译文.txt"
            bilingual_file = out_dir / f"{base_name}_中英对照.txt"
            failed_file = out_dir / f"{base_name}_失败段落.json"
            report_file = out_dir / f"{base_name}_任务报告.json"
            enc = self.cfg.get("output_encoding", "utf-8-sig")

            done_indices: list[int] = []
            failed_parts: list[dict] = []

            if checkpoint_file.exists():
                try:
                    cp = json.loads(checkpoint_file.read_text(encoding="utf-8"))
                    done_indices = [int(x) for x in cp.get("done_indices", [])]
                    failed_parts = list(cp.get("failed_parts", []))
                    self.log(f"断点恢复：已完成 {len(done_indices)} / {len(chunks)} 段", "success")
                except Exception as e:
                    self.log(f"读取断点失败，将创建新断点：{e}", "warning")

            done_set = set(done_indices)

            # If no checkpoint, initialize files immediately.
            if not checkpoint_file.exists():
                translated_file.write_text("", encoding=enc)
                bilingual_file.write_text("", encoding=enc)
                failed_file.write_text("[]", encoding="utf-8")
                self._write_checkpoint(checkpoint_file, input_path, done_indices, failed_parts, len(chunks), False)

            self.controller.start(len(chunks))
            self.controller.done = len(done_set)
            self.log(f"拆分完成：共 {len(chunks)} 段，每段上限 {max_chars} 字符", "success")

            manager = TranslateEngineManager(self.cfg, log_func=self.log)
            self.log("启用引擎：" + " / ".join(manager.available_engine_names()), "engine")

            # Show initial progress after checkpoint load.
            self.progress_signal.emit(
                self.controller.done,
                self.controller.total,
                self.controller.percent(),
                self.controller.elapsed(),
                self.controller.eta(),
            )

            for idx, chunk in enumerate(chunks, start=1):
                if idx in done_set:
                    continue

                if self.controller.cancelled:
                    self.log("任务已终止，停止后续翻译；已完成内容和 checkpoint.json 已保存", "cancel")
                    break

                self.controller.wait_if_paused()

                self.log(f"开始翻译第 {idx} / {len(chunks)} 段，字符数：{len(chunk)}", "start")

                try:
                    translated, engine_name = manager.translate(chunk, source=self.source_lang, target=self.target_lang)
                    translated_block = translated
                    bilingual_block = (
                        f"===== 第 {idx} 段 原文 =====\n{chunk}\n\n"
                        f"===== 第 {idx} 段 译文 / {engine_name} =====\n{translated}\n"
                    )
                    self.log(f"第 {idx} 段完成，引擎：{engine_name}", "success")
                except Exception as e:
                    failed_parts.append({"index": idx, "source": chunk, "error": str(e)})
                    translated_block = f"[第 {idx} 段翻译失败]\n{chunk}"
                    bilingual_block = (
                        f"===== 第 {idx} 段 原文 =====\n{chunk}\n\n"
                        f"===== 第 {idx} 段 译文失败 =====\n{e}\n"
                    )
                    self.log(f"第 {idx} 段失败：{e}", "error")

                # Realtime append. This is the key fix: output is written after every segment.
                with translated_file.open("a", encoding=enc) as f:
                    f.write(f"\n\n===== 第 {idx} 段 =====\n{translated_block}\n")
                with bilingual_file.open("a", encoding=enc) as f:
                    f.write("\n\n" + bilingual_block + "\n")

                done_indices.append(idx)
                done_set.add(idx)
                failed_file.write_text(json.dumps(failed_parts, ensure_ascii=False, indent=2), encoding="utf-8")
                self._write_checkpoint(checkpoint_file, input_path, done_indices, failed_parts, len(chunks), False)

                self.controller.step()
                self.progress_signal.emit(
                    self.controller.done,
                    self.controller.total,
                    self.controller.percent(),
                    self.controller.elapsed(),
                    self.controller.eta(),
                )

            completed = len(done_set) >= len(chunks) and not self.controller.cancelled
            self._write_checkpoint(checkpoint_file, input_path, done_indices, failed_parts, len(chunks), completed)

            report = {
                "input_file": str(input_path),
                "output_dir": str(out_dir),
                "total_chunks": len(chunks),
                "done_chunks": len(done_set),
                "failed_count": len(failed_parts),
                "elapsed": fmt_time(self.controller.elapsed()),
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "engines": manager.available_engine_names(),
                "source_lang": self.source_lang,
                "target_lang": self.target_lang,
                "cancelled": self.controller.cancelled,
                "completed": completed,
                "realtime_write": True,
                "checkpoint_file": str(checkpoint_file),
            }
            report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

            self.log(f"译文实时文件：{translated_file}", "success")
            self.log(f"中英对照实时文件：{bilingual_file}", "success")
            self.log(f"断点文件：{checkpoint_file}", "success")
            self.log(f"任务报告：{report_file}", "success")

            if failed_parts:
                self.log(f"存在失败段落：{len(failed_parts)} 段，已写入 {failed_file}", "warning")

            if self.controller.cancelled:
                self.finished_signal.emit(str(out_dir), f"任务已终止：已保存 {len(done_set)}/{len(chunks)} 段，可重新开始继续断点续译")
            else:
                self.finished_signal.emit(str(out_dir), f"任务完成：{len(done_set)}/{len(chunks)} 段")
        except Exception as e:
            self.failed_signal.emit(str(e))
