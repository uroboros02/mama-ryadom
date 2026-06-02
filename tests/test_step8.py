"""Шаг 8 — финал Блока 0: TZ Уфа, бот клиенту не пишет, полный прогон чек-листа.

Консолидированная приёмка «на трубах» (block-0.md) на искусственных входящих.
Проверка по логам/состоянию, не по диалогу: Блок 0 клиенту не пишет.
"""

from datetime import timedelta

from fastapi.testclient import TestClient

from app import config, main, router, state, memory, radar
from app.channel_max import InboundMessage
from app.fitbase import FitbaseWindow
from app.mocks.fitbase_mock import FitbaseMock
from app.mocks.alert_mock import AlertMock
from app.mocks.wazzup_mock import WazzupMock

client = TestClient(main.app)
GOOD = {"Authorization": f"Bearer {config.WAZZUP_WEBHOOK_SECRET}"}


def _win():
    return FitbaseWindow(FitbaseMock(), alert=AlertMock(), now=lambda: 0.0, sleep=lambda s: None)


def _env(mid, chat, text="привет", echo=False, phone=None):
    msg = {"messageId": mid, "chatType": "max", "chatId": chat, "text": text, "isEcho": echo}
    if phone:
        msg["contact"] = {"phone": phone}
    return {"messages": [msg]}


def _lead_of(chat):
    return router.lookup_lead_id(InboundMessage("x", "max", chat, "", None, True, None, None))


# ----- гр. 8: единый TZ Уфа -----
def test_tz_ufa_single_source():
    assert config.UFA_TZ.utcoffset(None) == timedelta(hours=5)
    memory.append("Lt", role="lead", text="x")
    assert memory.history("Lt")[0]["ts"].endswith("+05:00")


# ----- гр. 8: бот клиенту НЕ пишет -----
def test_block0_never_messages_client():
    sender = WazzupMock()
    main.set_sender(sender)
    main.set_window(_win())
    for i in range(3):
        client.post("/webhook", headers=GOOD, json=_env(f"c{i}", "chatA", "вопрос"))
    assert sender.sent == []  # после полного диалога — НИ ОДНОЙ отправки клиенту
    main.set_sender(None)
    main.set_window(None)


# ----- гр. 1+2+7: дубль не плодит лид и не двоит память -----
def test_dup_one_lead_one_memory():
    main.set_window(_win())
    client.post("/webhook", headers=GOOD, json=_env("d1", "chatB", "привет"))
    client.post("/webhook", headers=GOOD, json=_env("d1", "chatB", "привет"))  # ретрай
    lead = _lead_of("chatB")
    assert memory.count(lead) == 1
    main.set_window(None)


# ----- гр. 1: чужой вебхук отбит -----
def test_forged_webhook_rejected():
    r = client.post("/webhook", json=_env("x", "chatX"), headers={"Authorization": "Bearer wrong"})
    assert r.status_code == 401


# ----- гр. 2: два канала одного человека → один лид -----
def test_two_channels_one_lead():
    win = _win()
    main.set_window(win)
    client.post("/webhook", headers=GOOD, json=_env("p1", "chMax", "из MAX", phone="+79990000001"))
    # WhatsApp с тем же телефоном
    wa = {"messages": [{"messageId": "p2", "chatType": "whatsapp", "chatId": "chWa",
                        "text": "из WA", "isEcho": False, "contact": {"phone": "+79990000001"}}]}
    client.post("/webhook", headers=GOOD, json=wa)
    lead_max = _lead_of("chMax")
    lead_wa = router.lookup_lead_id(InboundMessage("x", "whatsapp", "chWa", "", None, True, None, None))
    assert lead_max == lead_wa
    main.set_window(None)


# ----- гр. 3: действующий клиент → к админу, лид не создаём -----
def test_active_client_to_admin():
    win = _win()
    win.client.seed_client("C1", contacts={"max": "vip"}, contract_active=True)
    main.set_window(win)
    client.post("/webhook", headers=GOOD, json=_env("v1", "vip", "привет"))
    assert router.lookup_lead_id(InboundMessage("x", "max", "vip", "", None, True, None, None)) is None
    main.set_window(None)


# ----- гр. 4: продавец → РУЧНОЙ; #старт → АВТО -----
def test_seller_manual_then_start():
    main.set_window(_win())
    client.post("/webhook", headers=GOOD, json=_env("s1", "chS", "привет"))
    lead = _lead_of("chS")
    client.post("/webhook", headers=GOOD, json=_env("s2", "chS", "продавец", echo=True))
    assert state.is_silenced(lead) is True
    client.post("/control", headers=GOOD, json={"lead_id": lead, "command": "#старт"})
    assert state.is_silenced(lead) is False
    main.set_window(None)


# ----- гр. 5: Fitbase лёг → бот не падает (кэш/эскалация) -----
def test_fitbase_down_survives():
    win = _win()
    alert = win.alert
    win.client.down = True
    assert win.get_lead("UNSEEN") is None  # не падаем
    assert len(alert.box) == 1             # эскалация ушла


# ----- гр. 6: радар без дублей -----
def test_radar_no_duplicates():
    win = _win()
    win.client.seed_lead("Lr", updated_at="2026-06-02T10:00:00+05:00")
    assert [l["id"] for l in radar.poll_once(win)] == ["Lr"]
    assert radar.poll_once(win) == []
