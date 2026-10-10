"""Unit-тесты заданий средней сложности № 6, 8 и 2."""

import os
import shutil
import tempfile
import tkinter as tk
import unittest

from file_dialog import (FileDialogApp, file_info, human_size, list_directory,
                         read_preview)
from progress_bar import MAXIMUM, ProgressApp, format_percent, next_value
from tests.gui import TkTestCase
from text_output import TextOutputApp, prepare_text


class TestProgressLogic(unittest.TestCase):
    """Проверка расчёта прогресса."""

    def test_next_value(self):
        """Значение растёт на шаг и не превышает максимум."""
        self.assertEqual(next_value(10, 5), 15)
        self.assertEqual(next_value(98, 5), MAXIMUM)

    def test_bad_step(self):
        """Неположительный шаг вызывает ValueError."""
        with self.assertRaises(ValueError):
            next_value(0, 0)

    def test_format_percent(self):
        """Проценты считаются от максимума."""
        self.assertEqual(format_percent(0), "0 %")
        self.assertEqual(format_percent(50), "50 %")
        self.assertEqual(format_percent(1, 3), "33 %")


class TestProgressWindow(TkTestCase):
    """Проверка окна с прогрессбаром."""

    def setUp(self):
        """Создать окно приложения."""
        super().setUp()
        self.app = ProgressApp(self.root)

    def test_ticks_until_done(self):
        """Шаги таймера доводят прогресс до 100 %."""
        self.app.speed.set(10)
        for _ in range(10):
            self.app.tick()
        self.assertEqual(self.app.value, MAXIMUM)
        self.assertEqual(self.app.progress["value"], MAXIMUM)
        self.assertIsNone(self.app.job)
        self.assertIn("Готово", self.app.status["text"])

    def test_pause_and_reset(self):
        """Пауза отменяет таймер, сброс обнуляет прогресс."""
        self.app.start()
        self.assertIsNotNone(self.app.job)
        self.app.tick()
        self.app.pause()
        self.assertIsNone(self.app.job)
        self.assertGreater(self.app.value, 0)
        self.app.reset()
        self.assertEqual(self.app.value, 0)
        self.assertEqual(self.app.percent["text"], "0 %")

    def test_indeterminate(self):
        """Кнопка ожидания включает и выключает второй прогрессбар."""
        self.app.toggle_wait()
        self.assertTrue(self.app.waiting)
        self.app.toggle_wait()
        self.assertFalse(self.app.waiting)


class TestFileHelpers(unittest.TestCase):
    """Проверка функций для работы с выбранным файлом."""

    def setUp(self):
        """Создать временную папку с файлами."""
        self.folder = tempfile.mkdtemp()

    def tearDown(self):
        """Удалить временную папку."""
        shutil.rmtree(self.folder)

    def make_file(self, name, data):
        """Создать файл с двоичным содержимым и вернуть путь к нему."""
        path = os.path.join(self.folder, name)
        with open(path, "wb") as file:
            file.write(data)
        return path

    def test_human_size(self):
        """Размеры переводятся в Б, КБ и МБ."""
        self.assertEqual(human_size(512), "512 Б")
        self.assertEqual(human_size(1536), "1.5 КБ")
        self.assertEqual(human_size(5 * 1024 ** 2), "5.0 МБ")
        with self.assertRaises(ValueError):
            human_size(-1)

    def test_file_info(self):
        """Сведения о файле содержат имя, размер и расширение."""
        path = self.make_file("notes.txt", b"hello")
        info = file_info(path)
        self.assertEqual(info["Имя"], "notes.txt")
        self.assertEqual(info["Размер"], "5 Б")
        self.assertEqual(info["Расширение"], ".txt")

    def test_preview_encodings(self):
        """Предпросмотр читает UTF-8 и Windows-1251."""
        utf = self.make_file("utf.txt", "Привет".encode("utf-8"))
        ansi = self.make_file("ansi.txt", "Привет".encode("cp1251"))
        self.assertEqual(read_preview(utf), ("Привет", False))
        self.assertEqual(read_preview(ansi), ("Привет", False))

    def test_preview_truncated(self):
        """Длинный файл обрезается до лимита."""
        path = self.make_file("long.txt", b"a" * 100)
        self.assertEqual(read_preview(path, limit=10), ("a" * 10, True))

    def test_preview_binary(self):
        """Для двоичного файла предпросмотр недоступен."""
        path = self.make_file("image.bin", b"\x89PNG\x00\x01\x02")
        with self.assertRaises(ValueError):
            read_preview(path)

    def test_list_directory(self):
        """Папки идут первыми, затем файлы по алфавиту."""
        self.make_file("b.txt", b"12")
        self.make_file("A.txt", b"1")
        os.mkdir(os.path.join(self.folder, "zdir"))
        names = [name for name, _, _ in list_directory(self.folder)]
        self.assertEqual(names, ["zdir", "A.txt", "b.txt"])


class TestFileDialogWindow(TkTestCase):
    """Проверка окна выбора файла (без открытия самих диалогов)."""

    def test_load_file(self):
        """Выбранный файл отображается в таблице и предпросмотре."""
        app = FileDialogApp(self.root)
        handle, path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            file.write("строка 1\nстрока 2")
        try:
            app.load_file(path)
            self.assertEqual(app.text.get("1.0", "end-1c"),
                             "строка 1\nстрока 2")
            self.assertEqual(len(app.info.get_children()), 5)
            self.assertEqual(app.status["text"], path)
        finally:
            os.remove(path)

    def test_unavailable_path(self):
        """Недоступный файл или папка не ломают окно."""
        app = FileDialogApp(self.root)
        missing = os.path.join(tempfile.gettempdir(), "нет_такого_пути")
        app.load_file(missing)
        self.assertIn("Не удалось открыть", app.text.get("1.0", "end"))
        app.show_text("")
        app.load_directory(missing)
        self.assertIn("Не удалось открыть", app.text.get("1.0", "end"))


class TestTextOutput(TkTestCase):
    """Проверка окна с текстовым полем и кнопкой."""

    def setUp(self):
        """Создать окно приложения."""
        super().setUp()
        self.app = TextOutputApp(self.root)

    def test_prepare_text(self):
        """Лишние пробелы убираются, пустая строка даёт None."""
        self.assertEqual(prepare_text("  Привет,   мир  "), "Привет, мир")
        self.assertIsNone(prepare_text("   "))

    def test_button_shows_text(self):
        """Нажатие кнопки выводит текст и добавляет его в историю."""
        self.app.entry.insert(0, "Привет")
        self.app.button.invoke()
        self.assertEqual(self.app.output["text"], "Привет")
        self.assertEqual(self.app.history.get(0, tk.END), ("Привет",))
        self.assertEqual(self.app.entry.get(), "")

    def test_empty_input(self):
        """Пустой ввод не попадает в историю."""
        self.app.button.invoke()
        self.assertIn("пустое", self.app.output["text"])
        self.assertEqual(self.app.history.size(), 0)

    def test_clear(self):
        """Очистка удаляет историю."""
        self.app.entry.insert(0, "текст")
        self.app.show_text()
        self.app.clear()
        self.assertEqual(self.app.history.size(), 0)
