"""Заглушка Fitbase (CRM) для Фазы А.

Изображает CRM в памяти процесса по контракту docs/fitbase-integration.md.
Реализует ровно те операции, что окно (app/fitbase) умеет в Блоке 0: найти/читать/
заметка(→ custom_fields)/задача. Бронь/оплата через API не создаются — их тут нет.

Переключатели отказа (для тестов предохранителей):
  · down=True            → каждый вызов как «Fitbase лёг» (FitbaseDown);
  · fail_429_times=N     → ближайшие N вызовов отвечают 429 (FitbaseRateLimited), потом ок.
"""

from app.fitbase import FitbaseDown, FitbaseRateLimited


class FitbaseMock:
    def __init__(self):
        self.leads = {}        # lead_id -> dict
        self.tasks = []        # созданные задачи
        self.down = False
        self.fail_429_times = 0

    # --- управление отказами ---
    def _maybe_fail(self):
        if self.down:
            raise FitbaseDown()
        if self.fail_429_times > 0:
            self.fail_429_times -= 1
            raise FitbaseRateLimited()

    # --- операции CRM (как у реального API v2) ---
    def get_lead(self, lead_id):
        self._maybe_fail()
        return self.leads.get(lead_id)

    def find_lead_by_channel(self, channel, value):
        self._maybe_fail()
        for lead in self.leads.values():
            if lead.get(channel) == value:
                return lead
        return None

    def create_task(self, **fields):
        self._maybe_fail()
        task = {"id": len(self.tasks) + 1, **fields}
        self.tasks.append(task)
        return task

    def patch_lead_custom_fields(self, lead_id, fields):
        self._maybe_fail()
        lead = self.leads.setdefault(lead_id, {"id": lead_id})
        lead.setdefault("custom_fields", {}).update(fields)
        return lead

    # --- помощник для тестов: засеять лид ---
    def seed_lead(self, lead_id, **fields):
        self.leads[lead_id] = {"id": lead_id, **fields}
        return self.leads[lead_id]
