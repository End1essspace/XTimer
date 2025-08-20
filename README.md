[ENG]

⏱️ XTimer

XTimer is a compact, customizable timer for Windows that sits right on the taskbar or next to it.
Perfect for work, gaming, streaming, cooking, or any task where you need a clear countdown always at hand.

## ✨ Features

* Floating timer always on top of other windows
* Horizontal or vertical orientation (automatically switches when moved to screen edges)
* Customizable appearance:

  * Dark/Light theme
  * Progress bar color
  * Font and size selection (up to 22pt)
* Context menu with time presets (from 1 second to several hours)
* User presets — save your own quick buttons
* System tray integration:

  * Show/Hide timer
  * Quick access to settings
* Notifications:

  * Flashing border when finished
  * Sound alert (.wav support)
* Auto-update via GitHub Releases or your own server
* State persistence — all settings and presets are saved between runs

📥 Installation

### 1. Run from source

```bash
git clone https://github.com/End1essspace/XTimer.git
cd XTimer
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

⚙️ Dependencies

* Python 3.9+
* PyQt5

All dependencies are listed in `requirements.txt`.

🔧 Settings

From the settings window you can:

* Enable/disable "always on top"
* Switch theme (dark/light)
* Change progress bar color
* Configure font and size
* Enable/disable auto-start when adding time
* Configure notifications:

  * Flashing frequency
  * Sound file
* Manage time presets

📦 Auto-updates

The program can:

* Check for updates on your own server (`SERVER_UPDATE_URL` in `constants.py`)
* If the server is unavailable — check GitHub Releases
* Suggest installation or download of the new version
  
🗂 Project Structure

```
XTimer/
 ├── icons/             # App and tray icons  
 ├── sounds/            # Notification sounds  
 ├── main.py            # Entry point  
 ├── timer.py           # Timer logic and rendering  
 ├── menu.py            # Context menu with time buttons  
 ├── dialogs.py         # Settings window  
 ├── utils.py           # Helpers (load/save presets)  
 ├── update_checker.py  # Auto-update module  
 ├── logging_config.py  # Logging  
 ├── winapi.py          # WinAPI interactions (taskbar position, etc.)  
 ├── constants.py       # Constants and paths  
 ├── requirements.txt  
 └── README.md  
```

📝 License

This project is licensed under the MIT License.

💡 Author

**XCON | RX**
TG: [@End1essspace](https://t.me/End1essspace)
GitHub: [End1essspace](https://github.com/End1essspace)


[RUS]


⏱ XTimer

XTimer — это компактный, настраиваемый таймер для Windows, который располагается прямо на панели задач или рядом с ней.  
Подходит для работы, игр, стримов, кулинарии и любых задач, где нужен наглядный отсчёт времени всегда под рукой.

✨ Возможности

- **Плавающий таймер поверх всех окон**
- **Горизонтальная или вертикальная ориентация** (автоматически меняется при перемещении к границам экрана)
- **Настраиваемый внешний вид**:
  - тёмная/светлая тема
  - цвет прогресс-бара
  - выбор шрифта и его размера (с ограничением до 22pt)
- **Контекстное меню с пресетами времени** (от 1 секунды до нескольких часов)
- **Пресеты пользователя** — сохранение своих кнопок
- **Системный трей**:
  - скрытие/показ таймера
  - быстрый доступ к настройкам
- **Оповещения**:
  - мигающая рамка по завершении
  - звуковой сигнал (поддержка `.wav`)
- **Автообновление** через GitHub Releases или ваш сервер
- **Запоминание состояния** (все настройки и пресеты сохраняются между запусками)

📥 Установка

### 1. Запуск из исходников
```bash
git clone https://github.com/End1essspace/XTimer.git
cd XTimer
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

⚙️ Зависимости
- Python 3.9+
- [PyQt5](https://pypi.org/project/PyQt5/)

Все зависимости перечислены в [`requirements.txt`](requirements.txt).

🔧 Настройки

Через окно настроек можно:
- Включить/отключить "всегда поверх окон"
- Задать тему (тёмная/светлая)
- Выбрать цвет прогресс-бара
- Настроить шрифт и его размер
- Включить/выключить автостарт при добавлении времени
- Настроить оповещения:
  - частота мигания
  - звуковой файл
- Управлять пресетами времени


📦 Автообновления
Программа умеет:
1. Проверять обновления с вашего сервера (`SERVER_UPDATE_URL` в `constants.py`)
2. Если сервер недоступен — проверять **GitHub Releases**
3. Предлагать установку или скачивание новой версии


🗂 Структура проекта
```
XTimer/
│
├── icons/              # Иконки приложения и трея
├── sounds/             # Звуки для оповещений
├── main.py             # Точка входа
├── timer.py            # Логика и отрисовка таймера
├── menu.py             # Контекстное меню с кнопками времени
├── dialogs.py          # Окно настроек
├── utils.py            # Хелперы (загрузка/сохранение пресетов)
├── update_checker.py   # Модуль автообновления
├── logging_config.py   # Логирование
├── winapi.py           # Взаимодействие с WinAPI (позиция taskbar и др.)
├── constants.py        # Константы и пути
├── requirements.txt
└── README.md
```

📝 Лицензия
Проект распространяется под лицензией [MIT](LICENSE).

💡 Автор
XCON | RX [TG:@End1essspace] 
[GitHub](https://github.com/End1essspace)
