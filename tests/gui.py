"""Общая основа для тестов окон Tkinter.

Главное окно Tk создаётся один раз на все тесты: повторное создание
Tk() в одном процессе на Windows иногда завершается ошибкой
инициализации Tcl. Каждый тест получает собственное окно Toplevel.
"""

import time
import tkinter as tk
import unittest

_root = None


def shared_root():
    """Вернуть общее скрытое главное окно, создав его при первом вызове."""
    global _root
    if _root is None:
        _root = tk.Tk()
        _root.withdraw()
    return _root


class TkTestCase(unittest.TestCase):
    """Создаёт скрытое окно Toplevel перед каждым тестом."""

    def setUp(self):
        """Создать окно или пропустить тест, если нет дисплея."""
        try:
            master = shared_root()
        except tk.TclError as error:
            self.skipTest(f"Tkinter недоступен: {error}")
        self.root = tk.Toplevel(master)
        self.root.withdraw()

    def tearDown(self):
        """Уничтожить окно после теста."""
        self.root.destroy()
        shared_root().update_idletasks()

    def wait_until(self, condition, timeout=3):
        """Обрабатывать события Tkinter, пока условие не выполнится."""
        deadline = time.monotonic() + timeout
        while not condition() and time.monotonic() < deadline:
            self.root.update()
            time.sleep(0.02)
        return condition()
