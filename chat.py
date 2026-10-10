"""Задание повышенной сложности № 10: локальный чат.

Сервер ChatServer работает на этом компьютере (адрес 127.0.0.1)
и пересылает сообщения всем подключённым клиентам по TCP-сокетам.
Окно ChatWindow на Tkinter отправляет сообщения на сервер и принимает
их в отдельном потоке. Tkinter нельзя вызывать из других потоков,
поэтому принятые сообщения передаются в окно через queue.Queue,
а окно забирает их по таймеру after.

Сообщения передаются как строки JSON, по одной на строку текста:
{"type": "message", "name": "Аня", "text": "Привет", "time": "12:30"}.

Запуск:
    python chat.py                  — демо: сервер и два окна чата;
    python chat.py server [порт]    — только сервер;
    python chat.py client Имя [порт] — окно клиента.
"""

import json
import queue
import socket
import sys
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import ttk

HOST = "127.0.0.1"
PORT = 5050
ENCODING = "utf-8"
MAX_NAME = 20


def encode_message(message):
    """Преобразовать словарь в строку JSON с переводом строки (bytes)."""
    return (json.dumps(message, ensure_ascii=False) + "\n").encode(ENCODING)


def decode_messages(buffer):
    """Выделить из буфера полные сообщения.

    Возвращает (список словарей, остаток буфера). Неполная последняя
    строка остаётся в буфере до следующего приёма данных, строки
    с некорректным JSON пропускаются.
    """
    *lines, rest = buffer.split(b"\n")
    messages = []
    for line in lines:
        if not line.strip():
            continue
        try:
            message = json.loads(line.decode(ENCODING))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if isinstance(message, dict):
            messages.append(message)
    return messages, rest


def now():
    """Вернуть текущее время в виде ЧЧ:ММ."""
    return datetime.now().strftime("%H:%M")


def clean_name(name):
    """Проверить имя пользователя и обрезать его до MAX_NAME символов."""
    name = " ".join(str(name or "").split())[:MAX_NAME]
    return name or "Гость"


def format_message(message):
    """Преобразовать сообщение в строку для вывода в окне чата."""
    stamp = message.get("time", "--:--")
    if message.get("type") == "system":
        return f"[{stamp}] * {message.get('text', '')}"
    return f"[{stamp}] {message.get('name', '?')}: {message.get('text', '')}"


class ChatServer:
    """Сервер чата: принимает клиентов и рассылает сообщения всем."""

    def __init__(self, host=HOST, port=PORT):
        """Открыть серверный сокет (port=0 — выбрать свободный порт)."""
        self._socket = socket.create_server((host, port))
        self.address = self._socket.getsockname()
        self._clients = {}
        self._lock = threading.Lock()
        self._send_lock = threading.Lock()
        self._running = False

    @property
    def port(self):
        """Порт, на котором работает сервер."""
        return self.address[1]

    def start(self):
        """Запустить приём подключений в фоновом потоке."""
        self._running = True
        threading.Thread(target=self._accept_loop, daemon=True).start()
        return self

    def stop(self):
        """Остановить сервер и отключить всех клиентов."""
        self._running = False
        self._socket.close()
        with self._lock:
            connections = list(self._clients)
            self._clients.clear()
        for connection in connections:
            connection.close()

    def users(self):
        """Вернуть отсортированный список имён подключённых клиентов."""
        with self._lock:
            return sorted(self._clients.values())

    def _accept_loop(self):
        """Принимать подключения, пока сервер работает."""
        while self._running:
            try:
                connection, _ = self._socket.accept()
            except OSError:
                break
            threading.Thread(target=self._serve_client,
                             args=(connection,), daemon=True).start()

    def _serve_client(self, connection):
        """Обслуживать одного клиента до его отключения."""
        name = None
        buffer = b""
        try:
            while True:
                data = connection.recv(4096)
                if not data:
                    break
                messages, buffer = decode_messages(buffer + data)
                for message in messages:
                    kind = message.get("type")
                    if kind == "join" and name is None:
                        name = self._register(connection, message.get("name"))
                    elif kind == "message" and name is not None:
                        text = str(message.get("text", "")).strip()
                        if text:
                            self.broadcast({"type": "message", "name": name,
                                            "text": text, "time": now()})
        except OSError:
            pass
        finally:
            self._unregister(connection, name)

    def _unique_name(self, name):
        """Добавить к имени номер, если такое имя уже занято."""
        taken = set(self._clients.values())
        candidate, number = name, 2
        while candidate in taken:
            candidate = f"{name} ({number})"
            number += 1
        return candidate

    def _register(self, connection, requested):
        """Добавить клиента и сообщить всем о его входе."""
        with self._lock:
            name = self._unique_name(clean_name(requested))
            self._clients[connection] = name
        self._send(connection, {"type": "welcome", "name": name})
        self.broadcast({"type": "system", "text": f"{name} вошёл в чат",
                        "time": now()})
        self.broadcast({"type": "users", "users": self.users()})
        return name

    def _unregister(self, connection, name):
        """Удалить клиента и сообщить остальным о его выходе."""
        with self._lock:
            removed = self._clients.pop(connection, None)
        connection.close()
        if removed is not None and self._running:
            self.broadcast({"type": "system", "text": f"{name} вышел из чата",
                            "time": now()})
            self.broadcast({"type": "users", "users": self.users()})

    def _send(self, connection, message):
        """Отправить сообщение одному клиенту.

        Отправка выполняется под блокировкой, чтобы сообщения из разных
        потоков не перемешивались в одном сокете.
        """
        try:
            with self._send_lock:
                connection.sendall(encode_message(message))
        except OSError:
            pass

    def broadcast(self, message):
        """Отправить сообщение всем подключённым клиентам."""
        with self._lock:
            connections = list(self._clients)
        for connection in connections:
            self._send(connection, message)


class ChatClient:
    """Сетевая часть клиента чата (без графического интерфейса)."""

    def __init__(self, name, on_message, host=HOST, port=PORT):
        """Запомнить параметры подключения и функцию-обработчик."""
        self.name = clean_name(name)
        self.on_message = on_message
        self.host = host
        self.port = port
        self._socket = None

    def connect(self, timeout=5):
        """Подключиться к серверу и запустить поток приёма сообщений."""
        self._socket = socket.create_connection((self.host, self.port),
                                                timeout=timeout)
        self._socket.settimeout(None)
        self._socket.sendall(encode_message({"type": "join",
                                             "name": self.name}))
        threading.Thread(target=self._read_loop, daemon=True).start()

    def send(self, text):
        """Отправить текст в чат. Пустые сообщения не отправляются."""
        text = text.strip()
        if not text or self._socket is None:
            return False
        try:
            self._socket.sendall(encode_message({"type": "message",
                                                 "text": text}))
        except OSError:
            return False
        return True

    def close(self):
        """Отключиться от сервера."""
        if self._socket is not None:
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self._socket.close()
            self._socket = None

    def _read_loop(self):
        """Принимать сообщения сервера и передавать их обработчику."""
        buffer = b""
        sock = self._socket
        try:
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                messages, buffer = decode_messages(buffer + data)
                for message in messages:
                    if message.get("type") == "welcome":
                        self.name = message.get("name", self.name)
                    self.on_message(message)
        except OSError:
            pass
        self.on_message({"type": "disconnected"})


class ChatWindow:
    """Окно чата на Tkinter."""

    POLL_MS = 100

    def __init__(self, window, name, host=HOST, port=PORT):
        """Создать виджеты окна и подключиться к серверу."""
        self.window = window
        self.inbox = queue.Queue()
        self.client = ChatClient(name, self.inbox.put, host, port)
        self.window.title(f"Чат — {self.client.name}")
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        main = ttk.Frame(window, padding=8)
        main.pack(fill=tk.BOTH, expand=True)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(0, weight=1)

        self.log = tk.Text(main, state=tk.DISABLED, wrap=tk.WORD,
                           width=50, height=18, font=("Segoe UI", 10))
        self.log.grid(row=0, column=0, sticky="nsew")
        self.log.tag_config("system", foreground="gray")
        self.log.tag_config("own", foreground="#1a5fb4")
        scroll = ttk.Scrollbar(main, command=self.log.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.log.config(yscrollcommand=scroll.set)

        side = ttk.Frame(main, padding=(8, 0, 0, 0))
        side.grid(row=0, column=2, sticky="ns")
        ttk.Label(side, text="В сети:").pack(anchor="w")
        self.users = tk.Listbox(side, width=16)
        self.users.pack(fill=tk.Y, expand=True)

        bottom = ttk.Frame(main, padding=(0, 8, 0, 0))
        bottom.grid(row=1, column=0, columnspan=3, sticky="we")
        self.entry = ttk.Entry(bottom)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind("<Return>", lambda event: self.send())
        self.send_button = ttk.Button(bottom, text="Отправить",
                                      command=self.send)
        self.send_button.pack(side=tk.LEFT, padx=(8, 0))

        try:
            self.client.connect()
        except OSError:
            self.append(f"Не удалось подключиться к серверу {host}:{port}",
                        "system")
            self.set_offline()
        else:
            self.entry.focus_set()
            self.window.after(self.POLL_MS, self.poll)

    def append(self, line, tag=None):
        """Добавить строку в окно сообщений."""
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, line + "\n", tag)
        self.log.config(state=tk.DISABLED)
        self.log.see(tk.END)

    def set_offline(self):
        """Заблокировать ввод после отключения от сервера."""
        self.entry.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)

    def send(self):
        """Отправить текст из поля ввода."""
        if self.client.send(self.entry.get()):
            self.entry.delete(0, tk.END)

    def handle(self, message):
        """Обработать одно сообщение от сервера."""
        kind = message.get("type")
        if kind == "welcome":
            self.window.title(f"Чат — {message['name']}")
        elif kind == "users":
            self.users.delete(0, tk.END)
            for user in message.get("users", []):
                self.users.insert(tk.END, user)
        elif kind == "system":
            self.append(format_message(message), "system")
        elif kind == "message":
            own = message.get("name") == self.client.name
            self.append(format_message(message), "own" if own else None)
        elif kind == "disconnected":
            self.append("Соединение с сервером закрыто", "system")
            self.set_offline()
            return False
        return True

    def poll(self):
        """Забрать сообщения из очереди и показать их в окне."""
        connected = True
        while True:
            try:
                message = self.inbox.get_nowait()
            except queue.Empty:
                break
            connected = self.handle(message) and connected
        if connected:
            self.window.after(self.POLL_MS, self.poll)

    def close(self):
        """Отключиться от сервера и закрыть окно."""
        self.client.close()
        self.window.destroy()


def run_server(port):
    """Запустить сервер в консоли до нажатия Ctrl+C."""
    server = ChatServer(HOST, port).start()
    print(f"Сервер чата запущен на {HOST}:{server.port}. Ctrl+C — выход.")
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nСервер остановлен")
    finally:
        server.stop()


def run_client(name, port):
    """Открыть окно клиента, подключённого к серверу на этом компьютере."""
    root = tk.Tk()
    ChatWindow(root, name, port=port)
    root.mainloop()


def run_demo():
    """Запустить сервер и два окна чата в одной программе."""
    server = ChatServer(HOST, 0).start()
    root = tk.Tk()
    ChatWindow(root, "Аня", port=server.port)
    second = tk.Toplevel(root)
    ChatWindow(second, "Борис", port=server.port)
    second.geometry("+620+80")
    root.mainloop()
    server.stop()


def main(argv=None):
    """Разобрать аргументы командной строки и запустить нужный режим."""
    args = sys.argv[1:] if argv is None else argv
    try:
        if not args:
            run_demo()
        elif args[0] == "server":
            run_server(int(args[1]) if len(args) > 1 else PORT)
        elif args[0] == "client" and len(args) > 1:
            run_client(args[1], int(args[2]) if len(args) > 2 else PORT)
        else:
            print(__doc__)
    except ValueError:
        print("Порт должен быть целым числом")
    except OSError as error:
        print(f"Ошибка сети: {error}")


if __name__ == "__main__":
    main()
