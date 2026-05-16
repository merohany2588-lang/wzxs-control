from __future__ import annotations

import time
import threading


class TaskController:
    def __init__(self):
        self.total = 0
        self.done = 0
        self.started_at: float | None = None
        self.cancelled = False
        self.paused = False
        self._pause_event = threading.Event()
        self._pause_event.set()

    def start(self, total: int) -> None:
        self.total = max(1, int(total))
        self.done = 0
        self.started_at = time.time()
        self.cancelled = False
        self.paused = False
        self._pause_event.set()

    def pause(self) -> None:
        self.paused = True
        self._pause_event.clear()

    def resume(self) -> None:
        self.paused = False
        self._pause_event.set()

    def cancel(self) -> None:
        self.cancelled = True
        self._pause_event.set()

    def wait_if_paused(self) -> None:
        self._pause_event.wait()

    def step(self) -> None:
        self.done += 1

    def elapsed(self) -> float:
        if self.started_at is None:
            return 0.0
        return time.time() - self.started_at

    def percent(self) -> float:
        if self.total <= 0:
            return 0.0
        return min(100.0, self.done / self.total * 100.0)

    def speed(self) -> float:
        elapsed = self.elapsed()
        if elapsed <= 0:
            return 0.0
        return self.done / elapsed

    def eta(self) -> float:
        spd = self.speed()
        if spd <= 0:
            return 0.0
        return (self.total - self.done) / spd
