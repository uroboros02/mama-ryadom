"""Поведенческий тест Шага 0 — рельсы стоят.

Проверяем ПОВЕДЕНИЕ, не код:
  1. сервер жив (/health = 200);
  2. труба принимает вброшенный вебхук (/webhook = 200);
  3. часовой пояс Уфа = UTC+5 (один источник правды);
  4. Redis-«понарошку» (fakeredis) пишет и читает.
"""

from datetime import timedelta

import fakeredis
from fastapi.testclient import TestClient

from app.main import app
from app.config import UFA_TZ

client = TestClient(app)


def test_health_alive():
    """Пульс есть: сервер отвечает 200 и говорит ok."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_webhook_accepts_fake_push():
    """Труба принимает вброшенный фейковый вебхук и подтверждает (быстрый ack)."""
    fake_push = {"messageId": "test-1", "text": "привет", "channel": "MAX"}
    resp = client.post("/webhook", json=fake_push)
    assert resp.status_code == 200


def test_ufa_timezone_is_utc_plus_5():
    """Часовой пояс Уфа = ровно UTC+5, заведён одним местом."""
    assert UFA_TZ.utcoffset(None) == timedelta(hours=5)


def test_fakeredis_roundtrip():
    """Redis-запаска (fakeredis) реально пишет и читает — память переживёт работу процесса."""
    r = fakeredis.FakeStrictRedis()
    r.set("проверка", "ок")
    assert r.get("проверка") == b"\xd0\xbe\xd0\xba"  # "ок" в UTF-8 байтах
