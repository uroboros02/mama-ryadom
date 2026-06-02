"""Поведенческий тест Шага 2 — идемпотентность по messageId.

Проверяем ПОВЕДЕНИЕ:
  1. already_processed(id) дважды → False (новый), затем True (повтор);
  2. один и тот же вебхук дважды → обработан ОДИН раз (второй помечен «повтор»), оба → 200;
  3. разные messageId → оба обрабатываются (защита не глушит легитимное);
  4. метка живёт в Redis (переживает «рестарт» процесса), не в памяти.
"""

import logging

import fakeredis
from fastapi.testclient import TestClient

from app.main import app
from app import config, redis_client, router

client = TestClient(app)
GOOD_AUTH = {"Authorization": f"Bearer {config.WAZZUP_WEBHOOK_SECRET}"}


def _envelope(message_id):
    return {"messages": [{
        "messageId": message_id, "chatType": "max", "chatId": "c1",
        "text": "привет", "isEcho": False,
    }]}


def test_already_processed_first_then_repeat():
    """Первый раз — новый (False), повтор — True."""
    assert router.already_processed("m1") is False
    assert router.already_processed("m1") is True


def test_duplicate_webhook_processed_once(caplog):
    """Один вебхук дважды → 'входящее' один раз + 'повтор' на второй; оба ответа 200."""
    with caplog.at_level(logging.INFO, logger="block0.webhook"):
        r1 = client.post("/webhook", json=_envelope("dup-1"), headers=GOOD_AUTH)
        r2 = client.post("/webhook", json=_envelope("dup-1"), headers=GOOD_AUTH)
    assert r1.status_code == 200 and r2.status_code == 200
    assert sum("входящее" in m for m in caplog.messages) == 1
    assert sum("повтор" in m for m in caplog.messages) == 1


def test_different_ids_both_processed(caplog):
    """Разные messageId → оба обработаны (не глушим легитимное)."""
    with caplog.at_level(logging.INFO, logger="block0.webhook"):
        client.post("/webhook", json=_envelope("a"), headers=GOOD_AUTH)
        client.post("/webhook", json=_envelope("b"), headers=GOOD_AUTH)
    assert sum("входящее" in m for m in caplog.messages) == 2


def test_mark_survives_restart():
    """Метка в Redis: новый клиент (как после рестарта) видит тот же ключ → повтор."""
    server = fakeredis.FakeServer()  # общее хранилище = настоящий Redis на сервере
    redis_client.set_redis(fakeredis.FakeStrictRedis(server=server))
    assert router.already_processed("persist-1") is False
    # «рестарт процесса»: новый клиент к тому же хранилищу
    redis_client.set_redis(fakeredis.FakeStrictRedis(server=server))
    assert router.already_processed("persist-1") is True
