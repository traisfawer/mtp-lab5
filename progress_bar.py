"""Задание средней сложности № 6: прогрессбар.

Окно Tkinter с виджетом ttk.Progressbar. Кнопка «Старт» запускает
имитацию длительной задачи: прогресс увеличивается по таймеру
root.after, поэтому окно не зависает. Есть пауза, сброс, регулировка
скорости и второй прогрессбар в неопределённом режиме (indeterminate).
"""

import tkinter as tk
from tkinter import ttk

MAXIMUM = 100
TICK_MS = 100


def next_value(value, step, maximum=MAXIMUM):
    """Вернуть следующее значение прогресса, не превышая maximum."""
    if step <= 0:
        raise ValueError("Шаг должен быть положительным")
    return min(value + step, maximum)


def format_percent(value, maximum=MAXIMUM):
    """Вернуть строку с процентом выполнения."""
    if maximum <= 0:
        raise ValueError("Максимум должен быть положительным")
    return f"{round(value / maximum * 100)} %"


class ProgressApp:
    """Окно с прогрессбаром и кнопками управления."""

    def __init__(self, root):
        """Создать виджеты окна."""
        self.root = root
        self.root.title("Прогрессбар — ЛР5, задание № 6")
        self.root.resizable(False, False)
        self.value = 0
        self.job = None
        self.waiting = False

        frame = ttk.Frame(root, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Имитация длительной задачи").grid(
            row=0, column=0, columnspan=3, sticky="w")
        self.progress = ttk.Progressbar(
            frame, length=360, maximum=MAXIMUM, mode="determinate")
        self.progress.grid(row=1, column=0, columnspan=3, pady=(8, 2))
        self.percent = ttk.Label(frame, text=format_percent(0))
        self.percent.grid(row=2, column=0, columnspan=3)

        ttk.Label(frame, text="Скорость:").grid(row=3, column=0, sticky="w")
        self.speed = tk.IntVar(value=3)
        tk.Scale(frame, from_=1, to=10, orient=tk.HORIZONTAL,
                 variable=self.speed, length=250).grid(
            row=3, column=1, columnspan=2, sticky="we")

        self.start_button = ttk.Button(frame, text="Старт",
                                       command=self.start)
        self.start_button.grid(row=4, column=0, pady=8)
        ttk.Button(frame, text="Пауза", command=self.pause).grid(
            row=4, column=1, pady=8)
        ttk.Button(frame, text="Сброс", command=self.reset).grid(
            row=4, column=2, pady=8)

        self.status = ttk.Label(frame, text="Нажмите «Старт»")
        self.status.grid(row=5, column=0, columnspan=3)

        ttk.Separator(frame).grid(row=6, column=0, columnspan=3,
                                  sticky="we", pady=10)
        ttk.Label(frame, text="Неопределённый режим (ожидание):").grid(
            row=7, column=0, columnspan=3, sticky="w")
        self.busy = ttk.Progressbar(frame, length=360, mode="indeterminate")
        self.busy.grid(row=8, column=0, columnspan=3, pady=8)
        self.wait_button = ttk.Button(frame, text="Запустить ожидание",
                                      command=self.toggle_wait)
        self.wait_button.grid(row=9, column=0, columnspan=3)

    def update_view(self):
        """Обновить прогрессбар и подпись с процентами."""
        self.progress["value"] = self.value
        self.percent.config(text=format_percent(self.value))

    def start(self):
        """Запустить или продолжить выполнение задачи."""
        if self.job is not None:
            return
        if self.value >= MAXIMUM:
            self.reset()
        self.status.config(text="Выполняется...")
        self.job = self.root.after(TICK_MS, self.tick)

    def tick(self):
        """Сделать один шаг задачи и запланировать следующий."""
        self.value = next_value(self.value, self.speed.get())
        self.update_view()
        if self.value >= MAXIMUM:
            self.job = None
            self.status.config(text="Готово! Задача выполнена")
            self.root.bell()
        else:
            self.job = self.root.after(TICK_MS, self.tick)

    def pause(self):
        """Приостановить выполнение задачи."""
        if self.job is not None:
            self.root.after_cancel(self.job)
            self.job = None
            self.status.config(text=f"Пауза на {format_percent(self.value)}")

    def reset(self):
        """Остановить задачу и обнулить прогресс."""
        self.pause()
        self.value = 0
        self.update_view()
        self.status.config(text="Прогресс сброшен")

    def toggle_wait(self):
        """Запустить или остановить индикатор ожидания."""
        if self.waiting:
            self.busy.stop()
            self.wait_button.config(text="Запустить ожидание")
        else:
            self.busy.start(10)
            self.wait_button.config(text="Остановить ожидание")
        self.waiting = not self.waiting


def main():
    """Открыть окно с прогрессбаром."""
    root = tk.Tk()
    ProgressApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
