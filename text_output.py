"""Задание средней сложности № 2: текстовое поле и кнопка, выводящая текст.

Пользователь вводит текст в поле Entry и нажимает кнопку «Вывести»
(или Enter) — текст появляется в метке Label и добавляется в историю.
Пустой ввод не принимается.
"""

import tkinter as tk
from tkinter import ttk


def prepare_text(text):
    """Убрать лишние пробелы; вернуть None для пустой строки."""
    cleaned = " ".join(text.split())
    return cleaned or None


class TextOutputApp:
    """Окно с полем ввода, кнопкой и областью вывода."""

    def __init__(self, root):
        """Создать виджеты окна."""
        self.root = root
        self.root.title("Вывод текста — ЛР5, задание № 2")
        self.root.minsize(420, 300)

        frame = ttk.Frame(root, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="Введите текст:").grid(
            row=0, column=0, columnspan=2, sticky="w")
        self.entry = ttk.Entry(frame, width=40)
        self.entry.grid(row=1, column=0, sticky="we", pady=5)
        self.entry.bind("<Return>", lambda event: self.show_text())
        self.entry.focus_set()

        self.button = ttk.Button(frame, text="Вывести",
                                 command=self.show_text)
        self.button.grid(row=1, column=1, padx=(8, 0))

        self.output = tk.Label(frame, text="Здесь появится текст",
                               font=("Segoe UI", 14), fg="gray",
                               wraplength=380, justify=tk.LEFT)
        self.output.grid(row=2, column=0, columnspan=2, sticky="w",
                         pady=10)

        ttk.Label(frame, text="История:").grid(
            row=3, column=0, columnspan=2, sticky="w")
        self.history = tk.Listbox(frame, height=6)
        self.history.grid(row=4, column=0, columnspan=2, sticky="nsew")
        frame.rowconfigure(4, weight=1)

        ttk.Button(frame, text="Очистить", command=self.clear).grid(
            row=5, column=1, sticky="e", pady=(8, 0))

    def show_text(self):
        """Вывести введённый текст в метку и историю."""
        text = prepare_text(self.entry.get())
        if text is None:
            self.output.config(text="Поле пустое — введите текст",
                               fg="red")
            return
        self.output.config(text=text, fg="black")
        self.history.insert(tk.END, text)
        self.entry.delete(0, tk.END)

    def clear(self):
        """Очистить поле ввода, вывод и историю."""
        self.entry.delete(0, tk.END)
        self.history.delete(0, tk.END)
        self.output.config(text="Здесь появится текст", fg="gray")


def main():
    """Открыть окно с текстовым полем и кнопкой."""
    root = tk.Tk()
    TextOutputApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
