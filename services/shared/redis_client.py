import redis


def get_redis(url: str) -> redis.Redis:
    return redis.from_url(url)
