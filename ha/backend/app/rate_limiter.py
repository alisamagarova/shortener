from __future__ import annotations

import redis


class RedisRateLimiter:
    """Rate limiting по IP через Redis (НФТ №3, №4): счётчик с фиксированным
    окном в 60 секунд.

    Счётчик хранится в Redis, а не в памяти процесса — поэтому лимит общий на
    все реплики backend за балансировщиком. В MVP-варианте (in-process dict)
    каждая реплика считала бы независимо, и реальный лимит вырос бы
    пропорционально числу реплик.
    """

    _window_seconds = 60

    def __init__(self, client: redis.Redis, max_requests_per_minute: int, key_prefix: str):
        self._client = client
        self._max_requests = max_requests_per_minute
        self._key_prefix = key_prefix

    def allow(self, client_ip: str) -> bool:
        key = f"{self._key_prefix}:{client_ip}"
        current = self._client.incr(key)
        if current == 1:
            self._client.expire(key, self._window_seconds)
        return current <= self._max_requests
