"""Заглушка Wazzup / MAX для Фазы А.

Изображает канал. В Блоке 0 бот клиенту НЕ пишет → метод send тут есть как «шов»
для F1, но в потоке Блока 0 он не вызывается (на этом проверяем гр. 8: 0 отправок).
"""


class WazzupMock:
    def __init__(self):
        self.sent = []  # отправленные клиенту сообщения (в Блоке 0 должно быть пусто)

    def send(self, chat_id, text):
        self.sent.append({"chat_id": chat_id, "text": text})
