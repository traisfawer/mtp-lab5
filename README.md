# Лабораторная работа № 5. Визуальное программирование на Python

**Ефимов Денис Борисович, группа 220042-11, вариант 6, лабораторная №5**

Дисциплина «Методы и технологии программирования» (часть 1).

## Задания варианта 6

Средней сложности:
- № 6 — прогрессбар — `progress_bar.py`;
- № 8 — диалог выбора файла — `file_dialog.py`;
- № 2 — окно с текстовым полем и кнопкой, выводящей текст — `text_output.py`.

Повышенной сложности:
- № 4 — график matplotlib внутри Tkinter — `plot_tk.py`;
- № 10 — программа чат (локальный) — `chat.py`.

## Описание

- `progress_bar.py` — `ttk.Progressbar` в режимах determinate и indeterminate;
  задача имитируется таймером `after`, поэтому окно не зависает;
  есть старт, пауза, сброс и регулировка скорости.
- `file_dialog.py` — диалоги `askopenfilename`, `askdirectory`,
  `asksaveasfilename`; для выбранного файла выводятся сведения
  (размер, дата изменения) и предпросмотр текста (UTF-8 / Windows-1251).
- `text_output.py` — `Entry` + `Button`: текст выводится в `Label`
  и сохраняется в истории (`Listbox`), работает и по клавише Enter.
- `plot_tk.py` — фигура matplotlib во фрейме Tkinter
  (`FigureCanvasTkAgg`, `NavigationToolbar2Tk`): выбор функции, диапазон,
  число точек, сетка, наложение графиков, координаты курсора.
- `chat.py` — сервер на TCP-сокетах (127.0.0.1) и окна клиентов на Tkinter;
  приём сообщений в отдельном потоке, передача в интерфейс через
  `queue.Queue`; список участников, уведомления о входе и выходе.

## Запуск

```
pip install -r requirements.txt

python progress_bar.py
python file_dialog.py
python text_output.py
python plot_tk.py
python chat.py
```

`python chat.py` без аргументов запускает сервер и сразу два окна чата.
Чат можно запустить и в разных окнах консоли:

```
python chat.py server
python chat.py client Аня
python chat.py client Борис
```

## Тесты

```
python -m pytest -v
```

или средствами стандартной библиотеки:

```
python -m unittest discover -s tests -t .
```

Логика программ проверяется без окон, окна — через скрытые окна Tkinter,
чат — на настоящих сокетах. Проверка стиля: `python -m flake8 .`
