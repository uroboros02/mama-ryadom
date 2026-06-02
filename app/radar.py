"""Радар двери B — опрос Fitbase (вебхуков у Fitbase нет). Шаг 7.

Дверь B = заявка появилась прямо в CRM (Тильда / VK Ads / руками). Бот узнаёт о ней
инкрементальным опросом по `updated_at`:
  · «закладка» (watermark) «докуда дочитал» живёт в Redis → переживает рестарт;
  · overlap-окно: опрашиваем чуть раньше закладки, чтобы не пропустить пограничные ts;
  · дедуп событий: каждое (lead_id + updated_at) обрабатываем один раз (атомарный SET NX),
    поэтому повторный опрос / рестарт / overlap НЕ дёргают одно и то же дважды.

Сам проактивный контакт по двери B (каскад MAX→WhatsApp→задача) — это F1, не Блок 0.
Здесь радар только НАДЁЖНО ДЕТЕКТИРУЕТ события без пропусков и без дублей.
"""

import logging
from datetime import datetime, timedelta

from app import config
from app.redis_client import get_redis

logger = logging.getLogger("block0.radar")

WATERMARK_KEY = "radar:watermark"
SEEN_TTL_SEC = 60 * 60 * 24  # дольше overlap-окна; авто-чистка отметок «видели»


def _decode(v):
    return v.decode() if isinstance(v, (bytes, bytearray)) else v


def _read_watermark():
    v = get_redis().get(WATERMARK_KEY)
    return _decode(v) if v is not None else None


def _write_watermark(ts_iso):
    get_redis().set(WATERMARK_KEY, ts_iso)


def _claim_event(lead_id, ts_iso) -> bool:
    """True, если это событие (lead+ts) видим ВПЕРВЫЕ (атомарно). Повтор → False."""
    return bool(get_redis().set(f"radar:seen:{lead_id}:{ts_iso}", "1",
                                nx=True, ex=SEEN_TTL_SEC))


def poll_once(window):
    """Один цикл опроса. Возвращает список новых/обновлённых лидов (без дублей)."""
    watermark = _read_watermark()
    if watermark:
        since = (datetime.fromisoformat(watermark)
                 - timedelta(seconds=config.RADAR_OVERLAP_SEC)).isoformat()
    else:
        since = None  # первый запуск — берём всё

    leads = window.list_leads_updated_since(since)
    if leads is None:
        # Fitbase лёг → цикл пропущен, закладку НЕ двигаем (повторим в следующий раз).
        return []

    new_events = []
    max_dt = datetime.fromisoformat(watermark) if watermark else None
    for lead in leads:
        ts = lead.get("updated_at")
        if not ts:
            continue
        if _claim_event(lead["id"], ts):
            new_events.append(lead)
            logger.info("дверь B: новый/обновлённый лид id=%s", lead["id"])
        dt = datetime.fromisoformat(ts)
        if max_dt is None or dt > max_dt:
            max_dt = dt

    if max_dt is not None:
        _write_watermark(max_dt.isoformat())
    return new_events
