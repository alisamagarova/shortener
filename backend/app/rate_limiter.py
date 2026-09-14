import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    """In-process ограничитель запросов по IP без Redis (НФТ №3, №4).

    Скользящее окно в 60 секунд: храним временные метки запросов на IP
    и отбрасываем те, что вышли за пределы окна.
    """

    def __init__(self, max_requests_per_minute: int):
        self._max_requests = max_requests_per_minute
        self._window_seconds = 60.0
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, client_ip: str) -> bool:
        now = time.monotonic()
        with self._lock:
            timestamps = self._requests[client_ip]
            while timestamps and now - timestamps[0] > self._window_seconds:
                timestamps.popleft()
            if len(timestamps) >= self._max_requests:
                return False
            timestamps.append(now)
            return True
