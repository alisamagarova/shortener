import threading
from collections import OrderedDict
from typing import Optional


class LRUCache:
    """Потокобезопасный in-process LRU-кэш code -> originalUrl (НФТ №5)."""

    def __init__(self, max_size: int):
        self._max_size = max_size
        self._data: OrderedDict[str, str] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            if key not in self._data:
                return None
            self._data.move_to_end(key)
            return self._data[key]

    def put(self, key: str, value: str) -> None:
        with self._lock:
            if key in self._data:
                self._data.move_to_end(key)
            self._data[key] = value
            if len(self._data) > self._max_size:
                self._data.popitem(last=False)

    def __len__(self) -> int:
        with self._lock:
            return len(self._data)
