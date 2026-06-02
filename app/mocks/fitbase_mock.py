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
        self.clients = {}      # client_id -> {contacts: {...}, contract_active: bool}
        self.tasks = []        # созданные задачи
        self._lead_seq = 0
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

    def find_active_client_by_contact(self, keys):
        """Действующий клиент с активным контрактом по надёжному ключу. Имя НЕ ключ."""
        self._maybe_fail()
        for client in self.clients.values():
            if not client.get("contract_active"):
                continue
            contacts = client.get("contacts", {})
            for k, v in keys.items():
                if v and contacts.get(k) == v:
                    return client
        return None

    def create_lead(self, **fields):
        self._maybe_fail()
        self._lead_seq += 1
        lead_id = f"L{self._lead_seq}"
        self.leads[lead_id] = {"id": lead_id, **fields}
        return self.leads[lead_id]

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

    # --- помощники для тестов ---
    def seed_lead(self, lead_id, **fields):
        self.leads[lead_id] = {"id": lead_id, **fields}
        return self.leads[lead_id]

    def seed_client(self, client_id, contacts, contract_active=True):
        self.clients[client_id] = {"id": client_id, "contacts": contacts,
                                   "contract_active": contract_active}
        return self.clients[client_id]
