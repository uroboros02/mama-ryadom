"""Окно Fitbase — единая дверь чтения/записи CRM (вся защита в одном месте).

На Фазе А поверх mock (app/mocks/fitbase_mock), на Фазе Б — поверх httpx-клиента
к реальному API v2 (контракт: docs/fitbase-integration.md). Логика окна одна и та же.

Предохранители (гр. 5 приёмочного чек-листа):
  · турникет ≤20 rps — не дать своему багу забить CRM (защита от нас, не от трафика);
  · бэк-офф на 429 — Fitbase притормозил → подождать и повторить;
  · кэш-запаска — Fitbase «лежит» → бот не падает: читаем из снимка, пишем НЕ фейкуем;
  · идемпотентность записей — задача/заметка не создаются дважды; всё пишется в лог.

По контракту v2 бронь/оплата через API не создаются → их тут нет (продавец руками, F3).
Факт лида пишем в `custom_fields` (Note в Fitbase привязан к клиенту, не к лиду).
"""

import json
import logging
import time

from app import config
from app.redis_client import get_redis

logger = logging.getLogger("block0.fitbase")


class FitbaseDown(Exception):
    """Fitbase недоступен (таймаут/5xx/сеть)."""


class FitbaseRateLimited(Exception):
    """Fitbase ответил 429 (слишком часто)."""


class RateLimiter:
    """Турникет: не выпускать больше max_rps запросов в секунду (равный интервал)."""

    def __init__(self, max_rps, now=time.monotonic, sleep=time.sleep):
        self.min_interval = 1.0 / max_rps
        self._now = now
        self._sleep = sleep
        self._last = None  # первый вызов проходит сразу (не тормозим на старте)

    def wait(self):
        if self._last is not None:
            gap = self._now() - self._last
            if gap < self.min_interval:
                self._sleep(self.min_interval - gap)
        self._last = self._now()


class FitbaseWindow:
    """Единая дверь к Fitbase. `client` — mock (Фаза А) или httpx-обёртка (Фаза Б)."""

    def __init__(self, client, redis=None, max_rps=None, alert=None,
                 now=time.monotonic, sleep=time.sleep, max_429_retries=3):
        self.client = client
        self.redis = redis or get_redis()
        self.alert = alert
        self.limiter = RateLimiter(max_rps or config.FITBASE_MAX_RPS, now=now, sleep=sleep)
        self._sleep = sleep
        self.max_429_retries = max_429_retries

    # --- обёртка любого сырого вызова: турникет + бэк-офф на 429 ---
    def _call(self, fn, *args, **kwargs):
        attempt = 0
        while True:
            self.limiter.wait()
            try:
                return fn(*args, **kwargs)
            except FitbaseRateLimited:
                attempt += 1
                if attempt > self.max_429_retries:
                    logger.error("Fitbase 429: исчерпаны попытки (%s) → пробрасываем", attempt)
                    raise
                backoff = 0.1 * (2 ** (attempt - 1))  # 0.1 / 0.2 / 0.4 ...
                logger.warning("Fitbase 429 → бэк-офф %.2fs (попытка %s)", backoff, attempt)
                self._sleep(backoff)

    # --- ЧТЕНИЕ (можно опереться на кэш-запаску) ---
    def get_lead(self, lead_id):
        """Прочитать карточку лида. Fitbase лёг → кэш-запаска; нет кэша → лог+эскалация, None."""
        key = f"cache:lead:{lead_id}"
        try:
            lead = self._call(self.client.get_lead, lead_id)
            if lead is not None:
                self.redis.set(key, json.dumps(lead))
            return lead
        except FitbaseDown:
            cached = self.redis.get(key)
            if cached:
                logger.warning("Fitbase недоступен → читаю из кэш-запаски: lead=%s", lead_id)
                return json.loads(cached)
            logger.error("Fitbase недоступен и кэша нет: lead=%s → эскалация", lead_id)
            self._escalate(f"Fitbase недоступен, нет кэша по лиду {lead_id}")
            return None

    def find_lead_by_channel(self, channel, value):
        """Найти лид по каналу. Fitbase лёг → None + лог (ведём осторожно, не падаем)."""
        try:
            return self._call(self.client.find_lead_by_channel, channel, value)
        except FitbaseDown:
            logger.warning("Fitbase недоступен при поиске лида (%s) → None", channel)
            return None

    def list_leads_updated_since(self, since_iso):
        """Лиды, изменённые с момента since_iso (радар двери B). None = Fitbase лёг."""
        try:
            return self._call(self.client.list_leads_updated_since, since_iso)
        except FitbaseDown:
            logger.warning("Fitbase недоступен — радар пропускает цикл (watermark не двигаем)")
            return None

    def active_client_by_contact(self, keys):
        """Действующий клиент с активным контрактом по надёжному ключу (телефон/id канала)?

        Fitbase лёг → не можем проверить → None (ведём как лида: ложно заглушить лида
        дороже, чем разок ответить действующему — см. философию ворот).
        """
        try:
            return self._call(self.client.find_active_client_by_contact, keys)
        except FitbaseDown:
            logger.warning("Fitbase недоступен при проверке клиента → считаем лидом")
            return None

    # --- ЗАПИСЬ (необратимое: идемпотентно + лог; кэш НЕ фейкуем) ---
    def create_task(self, idem_key, **fields):
        """Создать задачу продавцу. Идемпотентно по idem_key; Fitbase лёг → лог+эскалация."""
        if not self._claim_write(idem_key):
            logger.info("задача уже создана/в работе (идемпотентность): key=%s", idem_key)
            return None
        try:
            task = self._call(self.client.create_task, **fields)
            logger.info("создана задача: key=%s lead=%s", idem_key, fields.get("lead_id"))
            return task
        except FitbaseDown:
            self._release_write(idem_key)  # запись не прошла → дать повторить позже
            logger.error("Fitbase недоступен — задачу не записать: key=%s → эскалация", idem_key)
            self._escalate(f"Не удалось создать задачу {idem_key}: Fitbase недоступен")
            return None

    def create_lead(self, idem_key, **fields):
        """Создать лид (ПОДСТРАХОВКА — только когда не нашли). Идемпотентно + лог."""
        if not self._claim_write(idem_key):
            logger.info("лид уже создаётся (идемпотентность): key=%s", idem_key)
            return None
        try:
            lead = self._call(self.client.create_lead, **fields)
            logger.info("создан лид (подстраховка): key=%s id=%s", idem_key, lead.get("id"))
            return lead
        except FitbaseDown:
            self._release_write(idem_key)
            logger.error("Fitbase недоступен — лид не создать: key=%s → эскалация", idem_key)
            self._escalate(f"Не удалось создать лид {idem_key}: Fitbase недоступен")
            return None

    def add_note_fact(self, lead_id, idem_key, fields):
        """Записать факт лида в custom_fields. Идемпотентно; Fitbase лёг → лог+эскалация."""
        if not self._claim_write(idem_key):
            logger.info("факт уже записан (идемпотентность): key=%s", idem_key)
            return None
        try:
            res = self._call(self.client.patch_lead_custom_fields, lead_id, fields)
            logger.info("записан факт в custom_fields: key=%s lead=%s", idem_key, lead_id)
            return res
        except FitbaseDown:
            self._release_write(idem_key)
            logger.error("Fitbase недоступен — факт не записать: key=%s → эскалация", idem_key)
            self._escalate(f"Не удалось записать факт {idem_key}: Fitbase недоступен")
            return None

    # --- идемпотентность записи: атомарный claim, release при провале ---
    def _claim_write(self, idem_key):
        return bool(self.redis.set(f"fb:write:{idem_key}", "1", nx=True))

    def _release_write(self, idem_key):
        self.redis.delete(f"fb:write:{idem_key}")

    def _escalate(self, text):
        logger.warning("ЭСКАЛАЦИЯ: %s", text)
        if self.alert is not None:
            self.alert.push(text)
