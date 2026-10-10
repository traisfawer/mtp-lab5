"""Задание повышенной сложности № 4: график matplotlib внутри Tkinter.

Фигура matplotlib встраивается в окно Tkinter через FigureCanvasTkAgg,
под ней размещается стандартная панель инструментов
NavigationToolbar2Tk (масштаб, перемещение, сохранение в PNG).
Слева — панель управления: выбор функции, диапазон, число точек,
сетка и наложение нескольких графиков. Координаты курсора
выводятся в строке состояния.
"""

import tkinter as tk
from tkinter import ttk

import numpy as np
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
from matplotlib.figure import Figure

FUNCTIONS = {
    "sin(x)": np.sin,
    "cos(x)": np.cos,
    "x²": lambda x: x ** 2,
    "x³ − 3x": lambda x: x ** 3 - 3 * x,
    "exp(−x²)": lambda x: np.exp(-x ** 2),
    "ln(x)": np.log,
    "√x": np.sqrt,
    "sin(x)/x": lambda x: np.sinc(x / np.pi),
}


def parse_range(start_text, stop_text, points_text):
    """Проверить и преобразовать параметры построения.

    Возвращает (start, stop, points). При ошибке возбуждает ValueError
    с понятным сообщением.
    """
    try:
        start = float(start_text.replace(",", "."))
        stop = float(stop_text.replace(",", "."))
    except ValueError:
        raise ValueError("Границы диапазона должны быть числами") from None
    try:
        points = int(points_text)
    except ValueError:
        raise ValueError("Число точек должно быть целым") from None
    if start >= stop:
        raise ValueError("Начало диапазона должно быть меньше конца")
    if not 2 <= points <= 100_000:
        raise ValueError("Число точек должно быть от 2 до 100 000")
    return start, stop, points


def compute(name, start, stop, points):
    """Посчитать значения функции name на отрезке [start; stop].

    Точки вне области определения (например, x ≤ 0 для ln) получают
    значение NaN и не рисуются.
    """
    if name not in FUNCTIONS:
        raise ValueError(f"Неизвестная функция: {name}")
    x = np.linspace(start, stop, points)
    with np.errstate(divide="ignore", invalid="ignore"):
        y = FUNCTIONS[name](x)
    y = np.where(np.isfinite(y), y, np.nan)
    return x, y


class PlotApp:
    """Окно с панелью управления и встроенным графиком matplotlib."""

    def __init__(self, root):
        """Создать панель управления, фигуру и панель инструментов."""
        self.root = root
        self.root.title("График matplotlib в Tkinter — ЛР5, повышенная № 4")

        panel = ttk.Frame(root, padding=10)
        panel.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(panel, text="Функция:").pack(anchor="w")
        self.function = ttk.Combobox(panel, values=list(FUNCTIONS),
                                     state="readonly", width=18)
        self.function.current(0)
        self.function.pack(anchor="w", pady=(0, 8))

        self.start = self._entry(panel, "От:", "-10")
        self.stop = self._entry(panel, "До:", "10")
        self.points = self._entry(panel, "Точек:", "500")

        self.grid_on = tk.BooleanVar(value=True)
        ttk.Checkbutton(panel, text="Сетка", variable=self.grid_on,
                        command=self.toggle_grid).pack(anchor="w")
        self.overlay = tk.BooleanVar(value=False)
        ttk.Checkbutton(panel, text="Добавлять к графику",
                        variable=self.overlay).pack(anchor="w")

        ttk.Button(panel, text="Построить", command=self.plot).pack(
            fill=tk.X, pady=(12, 4))
        ttk.Button(panel, text="Очистить", command=self.clear).pack(
            fill=tk.X)

        self.message = ttk.Label(panel, text="", foreground="red",
                                 wraplength=170)
        self.message.pack(anchor="w", pady=10)

        plot_frame = ttk.Frame(root)
        plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.figure = Figure(figsize=(7, 5), dpi=100)
        self.axes = self.figure.add_subplot()
        self.canvas = FigureCanvasTkAgg(self.figure, master=plot_frame)
        self.toolbar = NavigationToolbar2Tk(self.canvas, plot_frame,
                                            pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.coords = ttk.Label(panel, text="x = —, y = —")
        self.coords.pack(side=tk.BOTTOM, anchor="w")
        self.canvas.mpl_connect("motion_notify_event", self.on_motion)

        self.prepare_axes()
        self.plot()

    def _entry(self, parent, label, value):
        """Создать подписанное поле ввода со значением по умолчанию."""
        ttk.Label(parent, text=label).pack(anchor="w")
        entry = ttk.Entry(parent, width=20)
        entry.insert(0, value)
        entry.pack(anchor="w", pady=(0, 8))
        return entry

    def prepare_axes(self):
        """Подписать оси и настроить сетку."""
        self.axes.set_xlabel("x")
        self.axes.set_ylabel("y")
        self.axes.axhline(0, color="gray", linewidth=0.8)
        self.axes.axvline(0, color="gray", linewidth=0.8)
        self.axes.grid(self.grid_on.get())

    def plot(self):
        """Построить выбранную функцию по параметрам из полей ввода."""
        try:
            start, stop, points = parse_range(
                self.start.get(), self.stop.get(), self.points.get())
        except ValueError as error:
            self.message.config(text=str(error))
            return
        name = self.function.get()
        x, y = compute(name, start, stop, points)
        if not self.overlay.get():
            self.axes.clear()
            self.prepare_axes()
        if np.all(np.isnan(y)):
            self.message.config(
                text=f"{name} не определена на этом отрезке")
        else:
            self.message.config(text="")
        self.axes.plot(x, y, label=name)
        self.axes.set_title(f"Отрезок [{start:g}; {stop:g}]")
        self.axes.legend(loc="best")
        self.canvas.draw()

    def clear(self):
        """Удалить все графики."""
        self.axes.clear()
        self.prepare_axes()
        self.message.config(text="")
        self.canvas.draw()

    def toggle_grid(self):
        """Включить или выключить сетку."""
        self.axes.grid(self.grid_on.get())
        self.canvas.draw()

    def on_motion(self, event):
        """Показать координаты курсора над графиком."""
        if event.inaxes is self.axes:
            self.coords.config(
                text=f"x = {event.xdata:.3f}, y = {event.ydata:.3f}")
        else:
            self.coords.config(text="x = —, y = —")


def main():
    """Открыть окно с графиком."""
    root = tk.Tk()
    PlotApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
