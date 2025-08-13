# logging_config.py
import logging
import os
import functools

def setup_logging(log_path: str = None) -> None:
    """
    Настраивает корневой логгер:
    – пишет в файл xtimer.log в папке проекта (если log_path не указан);
    – дублирует важные сообщения в stdout.
    """
    if log_path is None:
        base_dir = os.path.dirname(__file__)
        log_path = os.path.join(base_dir, "xtimer.log")

    # Формат: время, уровень, модуль, сообщение
    fmt = "%(asctime)s %(levelname)-8s [%(name)s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    # Общий хэндлер для файла
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(fmt, datefmt))

    # Хэндлер для консоли — только WARNING и выше
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter(fmt, datefmt))

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

def log_exceptions(func):
    """
    Декоратор: оборачивает функцию, логирует любые Exception с трассировкой.
    """
    logger = logging.getLogger(func.__module__)
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            logger.exception(f"Ошибка в {func.__name__}")
            raise
    return wrapper