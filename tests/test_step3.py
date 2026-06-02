"""Поведенческий тест Шага 3 — окно Fitbase и его предохранители (гр. 5 🔴).

Проверяем ПОВЕДЕНИЕ:
  1. турникет: >20 rps → окно само тормозит (равняет интервал);
  2. бэк-офф: Fitbase отдаёт 429 → окно ждёт и повторяет, в итоге успех;
  3. Fitbase «лёг» на чтении → бот не падает: отдаёт кэш-запаску;
  4. Fitbase «лёг», кэша нет → None + эскалация (алерт продавцу);
  5. запись (задача/факт) идемпотентна: один idem_key → одна запись;
  6. неудачная запись (Fitbase лёг) → НЕ помечена сделанной → повтор позже проходит.
"""

import logging

from app.fitbase import FitbaseWindow
from app.mocks.fitbase_mock import FitbaseMock
from app.mocks.alert_mock import AlertMock


class FakeClock:
    """Часы без реального сна: sleep лишь двигает время вперёд (тесты мгновенны)."""

    def __init__(self):
        self.t = 0.0
        self.slept = []

    def now(self):
        return self.t

    def sleep(self, s):
        self.slept.append(s)
        self.t += s


def _window(clock=None, max_rps=20, alert=None):
    clock = clock or FakeClock()
    mock = FitbaseMock()
    win = FitbaseWindow(mock, max_rps=max_rps, alert=alert,
                        now=clock.now, sleep=clock.sleep)
    return win, mock, clock


def test_turnstile_throttles_above_rps():
    """Три быстрых вызова подряд → окно вставило паузы ≈1/rps (тормозит)."""
    win, mock, clock = _window(max_rps=20)
    mock.seed_lead("L1", name="Аня")
    for _ in range(3):
        win.get_lead("L1")
    # между 3 вызовами — 2 паузы примерно по 0.05с (1/20)
    assert len(clock.slept) == 2
    assert all(abs(s - 0.05) < 1e-6 for s in clock.slept)


def test_429_backoff_then_success():
    """Fitbase дважды отдал 429 → окно подождало и повторило → запись прошла."""
    win, mock, clock = _window()
    mock.fail_429_times = 2
    task = win.create_task("t-429", lead_id="L1", description="перезвонить")
    assert task is not None
    assert len(mock.tasks) == 1
    assert clock.slept  # были паузы бэк-оффа


def test_down_read_falls_back_to_cache():
    """Fitbase лёг на чтении → бот не падает, отдаёт кэш-запаску прошлого чтения."""
    win, mock, _ = _window()
    mock.seed_lead("L1", name="Аня")
    first = win.get_lead("L1")          # успех → закэшировали
    assert first["name"] == "Аня"
    mock.down = True
    cached = win.get_lead("L1")         # Fitbase лёг → из кэша
    assert cached["name"] == "Аня"


def test_down_read_no_cache_escalates():
    """Fitbase лёг, кэша нет → None + алерт продавцу (эскалация)."""
    alert = AlertMock()
    win, mock, _ = _window(alert=alert)
    mock.down = True
    result = win.get_lead("UNSEEN")
    assert result is None
    assert len(alert.box) == 1


def test_task_idempotent():
    """Одна и та же задача (idem_key) дважды → создаётся ОДИН раз."""
    win, mock, _ = _window()
    win.create_task("once", lead_id="L1", description="перезвонить")
    second = win.create_task("once", lead_id="L1", description="перезвонить")
    assert second is None
    assert len(mock.tasks) == 1


def test_note_fact_idempotent():
    """Один и тот же факт (idem_key) дважды → пишется ОДИН раз."""
    win, mock, _ = _window()
    win.add_note_fact("L1", "age-set", {"возраст": "3"})
    again = win.add_note_fact("L1", "age-set", {"возраст": "3"})
    assert again is None
    assert mock.leads["L1"]["custom_fields"] == {"возраст": "3"}


def test_failed_write_can_retry_later():
    """Запись не прошла (Fitbase лёг) → не помечена сделанной → позже повтор проходит."""
    win, mock, _ = _window()
    mock.down = True
    assert win.create_task("retry-key", lead_id="L1") is None  # провал
    mock.down = False
    task = win.create_task("retry-key", lead_id="L1")           # тот же ключ — должен пройти
    assert task is not None
    assert len(mock.tasks) == 1


def test_write_is_logged(caplog):
    """Необратимая запись пишется в лог (аудит)."""
    win, mock, _ = _window()
    with caplog.at_level(logging.INFO, logger="block0.fitbase"):
        win.create_task("logme", lead_id="L1", description="x")
    assert any("создана задача" in m for m in caplog.messages)
