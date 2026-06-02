"""Поведенческий тест Шага 1 — канал MAX: замок + ack + перевод + метка.

Проверяем ПОВЕДЕНИЕ:
  1. поддельный/пустой Bearer → дверь отбивает (401), в обработку не идёт;
  2. валидный лид-вебхук → 200 сразу (быстрый ack);
  3. переводчик: реплика лида → is_from_lead=True;
  4. своя отправка (isEcho) → is_from_lead=False (стоп-кран метит);
  5. реплика продавца (authorId == продавец) → is_from_lead=False.
"""

from fastapi.testclient import TestClient

from app.main import app
from app import config, channel_max

client = TestClient(app)

GOOD_AUTH = {"Authorization": f"Bearer {config.WAZZUP_WEBHOOK_SECRET}"}

LEAD_PUSH = {
    "messageId": "abc-1",
    "chatType": "max",
    "chatId": "chat-777",
    "contact": {"phone": "+79990001122"},
    "text": "Здравствуйте, хочу записать ребёнка",
    "isEcho": False,
}


def test_webhook_rejects_bad_secret():
    """Чужой секрет → 401 (дверь публичная, замок держит)."""
    resp = client.post("/webhook", json=LEAD_PUSH, headers={"Authorization": "Bearer wrong"})
    assert resp.status_code == 401


def test_webhook_rejects_missing_auth():
    """Нет заголовка вовсе → 401."""
    resp = client.post("/webhook", json=LEAD_PUSH)
    assert resp.status_code == 401


def test_webhook_valid_fast_ack():
    """Валидный конверт messages[] → 200 сразу (быстрый ack)."""
    resp = client.post("/webhook", json={"messages": [LEAD_PUSH]}, headers=GOOD_AUTH)
    assert resp.status_code == 200


def test_webhook_test_ping_acked():
    """Пробный пинг подключения {test:true} → 200 (иначе Wazzup не сохранит URL)."""
    resp = client.post("/webhook", json={"test": True}, headers=GOOD_AUTH)
    assert resp.status_code == 200


def test_webhook_statuses_ignored():
    """Конверт статусов доставки → молча принят (200), не падаем."""
    resp = client.post("/webhook", json={"statuses": [{"messageId": "x", "status": "delivered"}]}, headers=GOOD_AUTH)
    assert resp.status_code == 200


def test_translate_lead_message():
    """Переводчик: реплика лида опознана как входящее лида + поля разобраны."""
    msg = channel_max.translate(LEAD_PUSH)
    assert msg.is_from_lead is True
    assert msg.message_id == "abc-1"
    assert msg.channel == "max"
    assert msg.chat_id == "chat-777"
    assert msg.phone == "+79990001122"


def test_translate_echo_not_from_lead():
    """Своя отправка (isEcho) → НЕ входящее лида (помечено)."""
    echo = {**LEAD_PUSH, "isEcho": True}
    msg = channel_max.translate(echo)
    assert msg.is_from_lead is False


def test_translate_seller_reply_not_from_lead(monkeypatch):
    """Реплика продавца (authorId == продавец) → НЕ входящее лида."""
    monkeypatch.setattr(config, "SELLER_AUTHOR_ID", "seller-99")
    seller_push = {**LEAD_PUSH, "authorId": "seller-99"}
    msg = channel_max.translate(seller_push)
    assert msg.is_from_lead is False
