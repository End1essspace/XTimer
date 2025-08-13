# utils.py
from PyQt5 import QtCore

# дефолтные пресеты (тоже, что и раньше)
RAW_DEFAULT_PRESETS = [
    {"name": "1S",  "minutes": 1},
    {"name": "5S",  "minutes": 5},
    {"name": "10S", "minutes": 10},
    {"name": "30S", "minutes": 30},
    {"name": "1M",  "minutes": 60},
    {"name": "5M",  "minutes": 300},
    {"name": "10M", "minutes": 600},
    {"name": "30M", "minutes": 1800},
    {"name": "1H",  "minutes": 3600},
    {"name": "2H",  "minutes": 7200},
    {"name": "3H",  "minutes": 10800},
    {"name": "5H",  "minutes": 18000},
]

def get_settings() -> QtCore.QSettings:
    """Единый QSettings для всего приложения."""
    return QtCore.QSettings("MyCompany", "TaskbarTimer")

def load_raw_presets() -> list[dict]:
    """
    Загружает список пресетов из QSettings (список dict {'name', 'minutes'}),
    или возвращает RAW_DEFAULT_PRESETS, если настроек нет или они некорректны.
    """
    settings = get_settings()
    raw = settings.value("presets/list", [], type=list)
    cleaned = []
    for item in raw:
        if isinstance(item, dict) and "name" in item and "minutes" in item:
            cleaned.append(item)
    return cleaned or RAW_DEFAULT_PRESETS

def load_presets() -> list[tuple[str,int]]:
    """Возвращает список пресетов в виде [(name, minutes), ...]."""
    return [(d["name"], d["minutes"]) for d in load_raw_presets()]

def save_presets(presets: list[dict | tuple]) -> None:
    """
    Сохраняет пресеты в QSettings.
    Аргумент — либо list[dict{'name','minutes'}], либо list[(name,minutes)].
    """
    dicts = []
    for item in presets:
        if isinstance(item, tuple):
            name, mins = item
        elif isinstance(item, dict):
            name, mins = item.get("name"), item.get("minutes")
        else:
            continue
        dicts.append({"name": name, "minutes": mins})
    get_settings().setValue("presets/list", dicts)
