"""Задание средней сложности № 8: диалог выбора файла.

Используются стандартные диалоги модуля tkinter.filedialog:
- askopenfilename — выбрать файл, показать сведения о нём
  и предпросмотр содержимого текстового файла;
- askdirectory — выбрать папку и вывести список её содержимого;
- asksaveasfilename — сохранить текст из предпросмотра в новый файл.
"""

import os
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, font, messagebox, ttk

FILE_TYPES = [
    ("Текстовые файлы", "*.txt *.md *.py *.csv *.log *.json"),
    ("Все файлы", "*.*"),
]
PREVIEW_LIMIT = 5000


def human_size(size):
    """Перевести размер в байтах в удобочитаемую строку."""
    if size < 0:
        raise ValueError("Размер не может быть отрицательным")
    if size < 1024:
        return f"{size} Б"
    value = float(size)
    for unit in ("КБ", "МБ", "ГБ"):
        value /= 1024
        if value < 1024 or unit == "ГБ":
            return f"{value:.1f} {unit}"


def file_info(path):
    """Вернуть словарь со сведениями о файле."""
    stat = os.stat(path)
    modified = datetime.fromtimestamp(stat.st_mtime)
    return {
        "Имя": os.path.basename(path),
        "Папка": os.path.dirname(os.path.abspath(path)),
        "Размер": human_size(stat.st_size),
        "Изменён": modified.strftime("%d.%m.%Y %H:%M"),
        "Расширение": os.path.splitext(path)[1] or "нет",
    }


def is_binary(path, probe=1024):
    """Проверить, похож ли файл на двоичный (есть нулевые байты)."""
    with open(path, "rb") as file:
        return b"\x00" in file.read(probe)


def read_preview(path, limit=PREVIEW_LIMIT):
    """Прочитать начало текстового файла.

    Возвращает пару (текст, обрезан_ли_файл). Пробует кодировки UTF-8
    и Windows-1251. Для двоичных файлов возбуждает ValueError.
    """
    if is_binary(path):
        raise ValueError("Файл не является текстовым")
    for encoding in ("utf-8", "cp1251"):
        try:
            with open(path, encoding=encoding) as file:
                text = file.read(limit + 1)
        except UnicodeDecodeError:
            continue
        return text[:limit], len(text) > limit
    raise ValueError("Не удалось определить кодировку файла")


def list_directory(path):
    """Вернуть содержимое папки: сначала папки, затем файлы."""
    entries = []
    for entry in os.scandir(path):
        try:
            if entry.is_dir():
                entries.append((entry.name, True, ""))
                continue
            size = human_size(entry.stat().st_size)
        except OSError:
            size = "нет доступа"
        entries.append((entry.name, False, size))
    return sorted(entries, key=lambda e: (not e[1], e[0].lower()))


class FileDialogApp:
    """Окно для работы с диалогами выбора файла и папки."""

    def __init__(self, root):
        """Создать виджеты окна."""
        self.root = root
        self.root.title("Диалог выбора файла — ЛР5, задание № 8")
        line = font.nametofont("TkDefaultFont").metrics("linespace")
        ttk.Style(root).configure("Treeview", rowheight=line + 6)

        buttons = ttk.Frame(root, padding=(10, 10, 10, 0))
        buttons.pack(fill=tk.X)
        ttk.Button(buttons, text="Открыть файл…",
                   command=self.open_file).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Выбрать папку…",
                   command=self.open_directory).pack(side=tk.LEFT, padx=6)
        ttk.Button(buttons, text="Сохранить как…",
                   command=self.save_as).pack(side=tk.LEFT)

        self.info = ttk.Treeview(root, columns=("value",), height=5)
        self.info.heading("#0", text="Параметр")
        self.info.heading("value", text="Значение")
        first = font.nametofont("TkDefaultFont").measure("Расширение")
        self.info.column("#0", width=first + 40, stretch=False)
        self.info.pack(fill=tk.X, padx=10, pady=10)

        text_frame = ttk.Frame(root)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        self.text = tk.Text(text_frame, wrap=tk.NONE, width=90, height=20,
                            font=("Consolas", 10))
        scroll = ttk.Scrollbar(text_frame, command=self.text.yview)
        self.text.config(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.status = ttk.Label(root, text="Файл не выбран", padding=10)
        self.status.pack(fill=tk.X)

    def show_info(self, rows):
        """Вывести пары «параметр — значение» в таблицу сведений."""
        self.info.delete(*self.info.get_children())
        for name, value in rows:
            self.info.insert("", tk.END, text=name, values=(value,))

    def show_text(self, text):
        """Заменить содержимое области предпросмотра."""
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", text)

    def show_error(self, path, error):
        """Сообщить, что файл или папку открыть не удалось."""
        self.show_info([("Ошибка", error.strerror or str(error))])
        self.show_text(f"Не удалось открыть:\n{path}\n\n{error}")
        self.status.config(text=path)

    def load_file(self, path):
        """Показать сведения о файле и его содержимое."""
        try:
            info = file_info(path)
        except OSError as error:
            self.show_error(path, error)
            return
        self.show_info(info.items())
        try:
            text, truncated = read_preview(path)
        except (OSError, ValueError) as error:
            self.show_text(f"Предпросмотр недоступен: {error}")
            self.status.config(text=path)
            return
        self.show_text(text)
        suffix = f" (показаны первые {PREVIEW_LIMIT} символов)" \
            if truncated else ""
        self.status.config(text=path + suffix)

    def open_file(self):
        """Открыть диалог выбора файла."""
        path = filedialog.askopenfilename(
            title="Выберите файл", filetypes=FILE_TYPES)
        if path:
            self.load_file(path)

    def load_directory(self, path):
        """Показать содержимое выбранной папки."""
        try:
            entries = list_directory(path)
        except OSError as error:
            self.show_error(path, error)
            return
        self.show_info([("Папка", path),
                        ("Подпапок", sum(1 for e in entries if e[1])),
                        ("Файлов", sum(1 for e in entries if not e[1]))])
        lines = [f"[папка] {name}" if is_dir else f"{name}  —  {size}"
                 for name, is_dir, size in entries]
        self.show_text("\n".join(lines) or "Папка пуста")
        self.status.config(text=path)

    def open_directory(self):
        """Открыть диалог выбора папки."""
        path = filedialog.askdirectory(title="Выберите папку")
        if path:
            self.load_directory(path)

    def save_as(self):
        """Сохранить текст предпросмотра в файл, выбранный в диалоге."""
        path = filedialog.asksaveasfilename(
            title="Сохранить как", defaultextension=".txt",
            filetypes=FILE_TYPES)
        if not path:
            return
        with open(path, "w", encoding="utf-8") as file:
            file.write(self.text.get("1.0", "end-1c"))
        messagebox.showinfo("Сохранение", f"Текст сохранён в файл\n{path}")


def main():
    """Открыть окно с диалогами выбора файла."""
    root = tk.Tk()
    FileDialogApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
