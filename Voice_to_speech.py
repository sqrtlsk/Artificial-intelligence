# Импортированные библиотеки и модули
import tkinter as tk
from tkinter import filedialog  # Модуль для работы с диалоговыми окнами
import sounddevice as sd  # Библиотека для записи и воспроизведения аудио
import queue  # Очередь для хранения аудиоданных
import json  # Для обработки JSON-данных
from vosk import Model, KaldiRecognizer  # Vosk - библиотека для распознавания речи

# Создание очереди для хранения аудиоданных и загрузка модели для распознавания речи
q = queue.Queue()  # Очередь для хранения аудиоданных
model = Model('vosk_model_s')  # Загрузка модели для распознавания речи

# Настройка аудиоустройства и выбор частоты дискретизации
device = sd.default.device = 1, 4  # Выбор аудиоустройства для записи (device[0] - вход, device[1] - выход)
samplerate = int(sd.query_devices(device[0], 'input')['default_samplerate'])  # Выбор частоты дискретизации

# Инициализация счетчиков слов и триггеров
word_count = {}  # Словарь для отслеживания количества повторений слов
TRIGGERS = {}  # Словарь для хранения триггеров, слов для удаления

# Функция для начала записи: отключает кнопку "Начать запись", включает "Закончить запись"
def start_recording():
    global recording, text_updating
    recording = True
    text_updating = True
    start_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)
    save_button.config(state=tk.DISABLED)

# Функция для завершения записи: включает кнопку "Начать запись", отключает "Закончить запись", включает "Сохранить"
def stop_recording():
    global recording, text_updating
    recording = False
    text_updating = False
    start_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)
    save_button.config(state=tk.NORMAL)

# Функция для сохранения текста в файл
def save_text():
    file_name = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])  # Открывается диалоговое окно для выбора файла
    if file_name:
        text_to_save = text_widget.get(1.0, tk.END)  # Получение текста из виджета
        with open(file_name, "w") as file:  # Открытие файла для записи
            file.write(text_to_save)  # Запись текста в файл
        save_button.config(state=tk.DISABLED)  # Отключение кнопки "Сохранить"

# Функция обратного вызова для обработки аудиоданных: добавляет данные в очередь, если запись включена
def callback(indata, frames, time, status):
    if recording:
        q.put(bytes(indata))

# Функция для преобразования текста: делает первую букву каждого предложения заглавной
def capitalize_after_period(text):
    parts = text.split('. ')
    for i, part in enumerate(parts):
        parts[i] = part.capitalize()
    return '. '.join(parts)

# Функция для распознавания текста и его обработки: учитывает триггеры и преобразует текст
def recognize(data):
    global text_widget
    words = data.split()
    for trigger in TRIGGERS:
        if trigger in words:
            TRIGGERS[trigger] += 1
            if TRIGGERS[trigger] == 3:
                selected_words[trigger] = 0
            words = [word for word in words if word != trigger]
    data = ' '.join(words)
    data = capitalize_after_period(data)
    text_widget.insert(tk.END, data + '. ')  # Добавление распознанного текста в виджет
    text_widget.see(tk.END)  # Прокрутка виджета до конца текста

# Функция для обновления текста в реальном времени
def update_text():
    if text_updating:
        data = q.get()  # Получение аудиоданных из очереди
        if rec.AcceptWaveform(data):
            data = json.loads(rec.Result())['text']  # Распознанный текст из JSON
            recognize(data)  # Обработка и добавление распознанного текста в виджет
    root.after(100, update_text)  # Повторный вызов функции через 100 миллисекунд

# Функция для обработки удаления выбранного текста: увеличивает счетчики и добавляет триггеры
def on_delete(event):
    selected_text = text_widget.get("sel.first", "sel.last")  # Получение выделенного текста
    if selected_text:
        word_count[selected_text] = word_count.get(selected_text, 0) + 1
        selected_words[selected_text] = selected_words.get(selected_text, 0) + 1
        if word_count[selected_text] == 3:
            TRIGGERS[selected_text] = selected_words[selected_text]  # Добавление триггера, если слово встречается 3 раза

# Создание окна программы
root = tk.Tk()
root.title("Распознавание и анализ речи")

# Создание текстового поля для вывода текста
text_widget = tk.Text(root, wrap=tk.WORD, width=60, height=20, bg='lightpink')
text_widget.pack()

# Создание кнопки "Начать запись" и привязка к ней функции start_recording
start_button = tk.Button(root, text="Начать запись", command=start_recording, bg='lightpink')
start_button.pack()

# Создание кнопки "Закончить запись" и привязка к ней функции stop_recording
stop_button = tk.Button(root, text="Закончить запись", command=stop_recording, state=tk.DISABLED, bg='lightpink')
stop_button.pack()

# Создание кнопки "Сохранить" и привязка к ней функции save_text
save_button = tk.Button(root, text="Сохранить", command=save_text, state=tk.DISABLED, bg='lightpink')
save_button.pack()

# Привязка функции on_delete к событию "Delete" (удаление текста)
text_widget.bind("<Delete>", on_delete)

# Запуск обновления текста в реальном времени
root.after(100, update_text)

# Запуск главного цикла
root.mainloop()

# Вывод триггеров после закрытия окна
print(TRIGGERS)
