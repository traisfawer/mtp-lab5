"""Unit-тесты заданий повышенной сложности № 4 и 10."""

import math
import queue
import unittest

import numpy as np

from chat import (ChatClient, ChatServer, ChatWindow, clean_name,
                  decode_messages, encode_message, format_message)
from plot_tk import FUNCTIONS, PlotApp, compute, parse_range
from tests.gui import TkTestCase

TIMEOUT = 3


class TestPlotLogic(unittest.TestCase):
    """Проверка расчёта данных для графика."""

    def test_parse_range(self):
        """Корректные параметры преобразуются в числа."""
        self.assertEqual(parse_range("-1,5", "2", "10"), (-1.5, 2.0, 10))

    def test_parse_range_errors(self):
        """Неверные параметры вызывают ValueError."""
        for args in (("a", "1", "10"), ("0", "1", "x"), ("5", "1", "10"),
                     ("0", "1", "1"), ("0", "1", "1000000")):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    parse_range(*args)

    def test_compute_values(self):
        """Значения функций считаются верно."""
        x, y = compute("x²", -2, 2, 5)
        self.assertEqual(list(x), [-2, -1, 0, 1, 2])
        self.assertEqual(list(y), [4, 1, 0, 1, 4])
        _, y = compute("sin(x)", 0, math.pi / 2, 2)
        self.assertAlmostEqual(y[-1], 1.0)

    def test_outside_domain(self):
        """Вне области определения получаются NaN."""
        _, y = compute("ln(x)", -1, 1, 3)
        self.assertTrue(np.isnan(y[0]))
        self.assertTrue(np.isnan(y[1]))
        self.assertAlmostEqual(y[2], 0.0)

    def test_all_functions(self):
        """Все функции из списка строятся без ошибок."""
        for name in FUNCTIONS:
            with self.subTest(name=name):
                x, y = compute(name, 0.5, 3, 50)
                self.assertEqual(len(y), 50)

    def test_unknown_function(self):
        """Неизвестная функция вызывает ValueError."""
        with self.assertRaises(ValueError):
            compute("tg(x)", 0, 1, 10)


class TestPlotWindow(TkTestCase):
    """Проверка окна с графиком."""

    def setUp(self):
        """Создать окно приложения."""
        super().setUp()
        self.app = PlotApp(self.root)

    def test_initial_plot(self):
        """При запуске строится график функции по умолчанию."""
        self.assertEqual(len(self.app.axes.get_lines()), 3)

    def test_overlay(self):
        """С флажком наложения графики добавляются."""
        self.app.overlay.set(True)
        self.app.function.set("cos(x)")
        self.app.plot()
        labels = [line.get_label() for line in self.app.axes.get_lines()]
        self.assertIn("sin(x)", labels)
        self.assertIn("cos(x)", labels)

    def test_bad_input_message(self):
        """Ошибка ввода выводится в окне, график не меняется."""
        self.app.start.delete(0, "end")
        self.app.start.insert(0, "abc")
        self.app.plot()
        self.assertIn("числами", self.app.message["text"])

    def test_clear(self):
        """Очистка удаляет графики функций."""
        self.app.clear()
        labels = [line.get_label() for line in self.app.axes.get_lines()]
        self.assertNotIn("sin(x)", labels)


class TestChatProtocol(unittest.TestCase):
    """Проверка формата сообщений чата."""

    def test_round_trip(self):
        """Сообщение кодируется и декодируется без изменений."""
        message = {"type": "message", "name": "Аня", "text": "Привет"}
        messages, rest = decode_messages(encode_message(message))
        self.assertEqual(messages, [message])
        self.assertEqual(rest, b"")

    def test_partial_buffer(self):
        """Неполное сообщение остаётся в буфере."""
        data = encode_message({"type": "a"}) + encode_message({"type": "b"})
        messages, rest = decode_messages(data[:-5])
        self.assertEqual(messages, [{"type": "a"}])
        messages, rest = decode_messages(rest + data[-5:])
        self.assertEqual(messages, [{"type": "b"}])

    def test_invalid_lines_skipped(self):
        """Некорректный JSON пропускается."""
        data = b"not json\n[1, 2]\n" + encode_message({"type": "ok"})
        messages, _ = decode_messages(data)
        self.assertEqual(messages, [{"type": "ok"}])

    def test_clean_name(self):
        """Имя очищается от пробелов и ограничивается по длине."""
        self.assertEqual(clean_name("  Аня  "), "Аня")
        self.assertEqual(clean_name(""), "Гость")
        self.assertEqual(len(clean_name("x" * 50)), 20)

    def test_format_message(self):
        """Обычные и системные сообщения форматируются по-разному."""
        self.assertEqual(format_message({"type": "message", "name": "Аня",
                                         "text": "Привет", "time": "12:00"}),
                         "[12:00] Аня: Привет")
        self.assertEqual(format_message({"type": "system", "text": "вход",
                                         "time": "12:00"}),
                         "[12:00] * вход")


class TestChatNetwork(unittest.TestCase):
    """Проверка сервера и клиентов на настоящих сокетах."""

    def setUp(self):
        """Запустить сервер на свободном порту."""
        self.server = ChatServer(port=0).start()
        self.clients = []

    def tearDown(self):
        """Отключить клиентов и остановить сервер."""
        for client in self.clients:
            client.close()
        self.server.stop()

    def connect(self, name):
        """Подключить клиента, вернуть его и очередь его сообщений."""
        inbox = queue.Queue()
        client = ChatClient(name, inbox.put, port=self.server.port)
        client.connect()
        self.clients.append(client)
        return client, inbox

    def wait_for(self, inbox, kind, **fields):
        """Дождаться сообщения нужного типа с нужными полями."""
        while True:
            message = inbox.get(timeout=TIMEOUT)
            if message.get("type") == kind and all(
                    message.get(k) == v for k, v in fields.items()):
                return message

    def test_join_and_broadcast(self):
        """Сообщение одного клиента получают все."""
        anya, anya_inbox = self.connect("Аня")
        self.wait_for(anya_inbox, "welcome", name="Аня")
        boris, boris_inbox = self.connect("Борис")
        self.wait_for(boris_inbox, "welcome", name="Борис")
        self.wait_for(anya_inbox, "system", text="Борис вошёл в чат")
        self.wait_for(anya_inbox, "users", users=["Аня", "Борис"])

        anya.send("Привет, Борис!")
        for inbox in (anya_inbox, boris_inbox):
            message = self.wait_for(inbox, "message")
            self.assertEqual(message["name"], "Аня")
            self.assertEqual(message["text"], "Привет, Борис!")

    def test_unique_names(self):
        """Одинаковые имена получают номер."""
        _, first = self.connect("Аня")
        self.wait_for(first, "welcome", name="Аня")
        second_client, second = self.connect("Аня")
        self.wait_for(second, "welcome", name="Аня (2)")
        self.assertEqual(second_client.name, "Аня (2)")

    def test_leave(self):
        """Остальные узнают о выходе клиента."""
        _, anya_inbox = self.connect("Аня")
        self.wait_for(anya_inbox, "welcome")
        boris, boris_inbox = self.connect("Борис")
        self.wait_for(boris_inbox, "welcome")
        boris.close()
        self.wait_for(anya_inbox, "system", text="Борис вышел из чата")
        self.wait_for(anya_inbox, "users", users=["Аня"])

    def test_empty_message_not_sent(self):
        """Пустое сообщение не отправляется."""
        client, _ = self.connect("Аня")
        self.assertFalse(client.send("   "))


class TestChatWindow(TkTestCase):
    """Проверка окна чата."""

    def setUp(self):
        """Запустить сервер и открыть окно клиента."""
        super().setUp()
        self.server = ChatServer(port=0).start()
        self.window = ChatWindow(self.root, "Аня", port=self.server.port)

    def tearDown(self):
        """Отключить клиента и остановить сервер."""
        self.window.client.close()
        self.server.stop()
        super().tearDown()

    def test_message_shown(self):
        """Отправленное сообщение появляется в окне."""
        self.window.entry.insert(0, "Всем привет")
        self.window.send()
        self.assertEqual(self.window.entry.get(), "")
        self.wait_until(lambda: "Аня: Всем привет"
                        in self.window.log.get("1.0", "end"))
        self.assertIn("Аня: Всем привет", self.window.log.get("1.0", "end"))
        self.assertEqual(self.window.users.get(0, "end"), ("Аня",))

    def test_server_unavailable(self):
        """Без сервера окно сообщает об ошибке и блокирует ввод."""
        port = self.server.port
        self.server.stop()
        self.server = ChatServer(port=0).start()
        other = ChatWindow(self.root, "Борис", port=port)
        self.assertIn("Не удалось подключиться",
                      other.log.get("1.0", "end"))
        self.assertEqual(str(other.send_button["state"]), "disabled")
