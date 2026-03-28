import time


class TTLCache:

    def __init__(self):
        self._storage = {}

    def get(self, key):
        value = self._storage.get(key)
        if not value:
            return None

        data, expire_time = value

        if time.time() > expire_time:
            del self._storage[key]
            return None

        return data

    def set(self, key, value, ttl: int):
        expire_time = time.time() + ttl
        self._storage[key] = (value, expire_time)