"""Общие фикстуры тестов.

Каждому тесту — чистый fakeredis вместо настоящего Redis, чтобы тесты не зависели
от запущенного сервера и не текли друг в друга.
"""

import fakeredis
import pytest

from app import redis_client


@pytest.fixture(autouse=True)
def fresh_redis():
    redis_client.set_redis(fakeredis.FakeStrictRedis())
    yield
    redis_client.set_redis(None)
