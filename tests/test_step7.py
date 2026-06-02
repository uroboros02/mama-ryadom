"""Поведенческий тест Шага 7 — радар двери B (опрос Fitbase) (гр. 6 🔴).

Проверяем ПОВЕДЕНИЕ:
  1. новый лид в окне → радар видит его как новое событие;
  2. повторный опрос → тот же лид НЕ дёргается дважды (дедуп);
  3. рестарт (новый клиент к тому же Redis) → без дублей (watermark+seen переживают);
  4. обновлённый лид (новый updated_at) → снова детектируется;
  5. равные timestamp у двух лидов → оба по разу, повтор → ноль;
  6. Fitbase лёг → цикл пропущен (watermark не двигаем), после восстановления лид виден.
"""

from datetime import datetime, timedelta

import fakeredis

from app import config, radar, redis_client
from app.fitbase import FitbaseWindow
from app.mocks.fitbase_mock import FitbaseMock


def _win(mock=None):
    mock = mock or FitbaseMock()
    win = FitbaseWindow(mock, now=lambda: 0.0, sleep=lambda s: None)
    return win, mock


def _ts(offset_sec):
    """ISO-время в зоне Уфа со сдвигом в секундах (для порядка)."""
    base = datetime(2026, 6, 2, 10, 0, 0, tzinfo=config.UFA_TZ)
    return (base + timedelta(seconds=offset_sec)).isoformat()


def test_new_lead_detected():
    win, mock = _win()
    mock.seed_lead("L1", updated_at=_ts(0))
    events = radar.poll_once(win)
    assert [l["id"] for l in events] == ["L1"]


def test_repeat_poll_no_duplicate():
    win, mock = _win()
    mock.seed_lead("L1", updated_at=_ts(0))
    radar.poll_once(win)
    assert radar.poll_once(win) == []  # дедуп: второй раз не дёргаем


def test_restart_no_duplicate():
    """Рестарт нашего процесса (новый клиент к тому же Redis) → без повторного касания."""
    server = fakeredis.FakeServer()
    redis_client.set_redis(fakeredis.FakeStrictRedis(server=server))
    win, mock = _win()
    mock.seed_lead("L1", updated_at=_ts(0))
    radar.poll_once(win)
    redis_client.set_redis(fakeredis.FakeStrictRedis(server=server))  # «рестарт»
    assert radar.poll_once(win) == []


def test_updated_lead_detected_again():
    """Лид изменился (новый updated_at) → радар видит обновление."""
    win, mock = _win()
    mock.seed_lead("L1", updated_at=_ts(0))
    radar.poll_once(win)
    mock.leads["L1"]["updated_at"] = _ts(300)  # лид обновили позже
    events = radar.poll_once(win)
    assert [l["id"] for l in events] == ["L1"]


def test_equal_timestamps_each_once():
    win, mock = _win()
    mock.seed_lead("L1", updated_at=_ts(0))
    mock.seed_lead("L2", updated_at=_ts(0))  # одинаковый ts
    events = radar.poll_once(win)
    assert {l["id"] for l in events} == {"L1", "L2"}
    assert radar.poll_once(win) == []  # повтор → ноль


def test_fitbase_down_skips_cycle():
    """Fitbase лёг → цикл пропущен; после восстановления лид всё равно виден (не потерян)."""
    win, mock = _win()
    mock.seed_lead("L1", updated_at=_ts(0))
    mock.down = True
    assert radar.poll_once(win) == []
    assert redis_client.get_redis().get(radar.WATERMARK_KEY) is None  # закладку не двигали
    mock.down = False
    assert [l["id"] for l in radar.poll_once(win)] == ["L1"]
