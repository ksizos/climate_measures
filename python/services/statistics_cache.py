_CACHE_KEY = 0


def statistics_cache_key() -> int:
    return _CACHE_KEY


def invalidate_statistics_cache() -> None:
    global _CACHE_KEY
    _CACHE_KEY += 1
