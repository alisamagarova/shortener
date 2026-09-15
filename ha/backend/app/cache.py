from __future__ import annotations

import redis


class RedisCache:
    """Кэш code -> originalUrl в Redis, общий для всех реплик backend.

    Вытеснение (LRU, НФТ №5) настраивается на самом сервере Redis через
    maxmemory + maxmemory-policy=allkeys-lru (см. docker-compose.yml), а не в
    приложении — в отличие от in-process OrderedDict в MVP-варианте, тут кэш
    переживает перезапуск/деплой отдельной реплики backend и виден всем сразу.
    """

    _KEY_PREFIX = "shortener:link:"

    def __init__(self, client: redis.Redis):
        self._client = client

    def get(self, key: str) -> str | None:
        value = self._client.get(self._KEY_PREFIX + key)
        return value.decode() if value is not None else None

    def put(self, key: str, value: str) -> None:
        self._client.set(self._KEY_PREFIX + key, value)
