from __future__ import annotations

from pathlib import Path
from threading import Lock, Timer
from typing import Callable

from ..models import ProjectSession
from .serializer import save_session


class SessionAutosaver:
    def __init__(
        self,
        session_provider: Callable[[], ProjectSession],
        path: Path,
        *,
        interval_seconds: float = 30,
    ) -> None:
        self._session_provider = session_provider
        self._path = path
        self._interval = max(1.0, interval_seconds)
        self._timer: Timer | None = None
        self._dirty = False
        self._lock = Lock()

    def mark_dirty(self) -> None:
        with self._lock:
            self._dirty = True
            if self._timer is None:
                self._timer = Timer(self._interval, self.flush)
                self._timer.daemon = True
                self._timer.start()

    def flush(self) -> None:
        with self._lock:
            timer, self._timer = self._timer, None
            dirty, self._dirty = self._dirty, False
        if timer:
            timer.cancel()
        if dirty:
            save_session(self._session_provider(), self._path)

    def close(self) -> None:
        self.flush()

    def cancel(self) -> None:
        with self._lock:
            timer, self._timer = self._timer, None
            self._dirty = False
        if timer:
            timer.cancel()
