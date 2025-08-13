from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtGui     import QPixmap, QColor, QPainter, QIcon
from PyQt5.QtWidgets import QStyle, QSizePolicy, QVBoxLayout
from logging_config import log_exceptions

class TimerMenu(QtWidgets.QWidget):
    """
    Контекстное меню таймера: кнопки add-time, start/pause, reset, custom-time.
    """

    add_time     = QtCore.pyqtSignal(int)  # +N секунд
    start_pause  = QtCore.pyqtSignal()     # переключить run/pause
    reset_signal = QtCore.pyqtSignal()     # сброс
    custom_time  = QtCore.pyqtSignal()     # открыть TimeDialog

    @log_exceptions
    def __init__(self, parent, presets=None):
        super().__init__(parent,
            QtCore.Qt.Tool |
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint
        )

        # ————————————————————————————————————————————————
        # Общий стиль
        self.setStyleSheet(
            # фон #2B2B2B, текст #EAEAEA, рамка #4B8BBE 1px
            "QWidget{"
                "background:#2B2B2B;"
                "color:#EAEAEA;"
                "border:1px solid #4B8BBE;"
                "border-radius:6px;"
            "}"
            # у кнопок чуть сглаженный стиль (скругл. 4px)
            "QPushButton{"
                "min-width:32px;"
                "padding:4px;"
                "border:1px solid #555555;"
                "border-radius:4px;"
                "background:transparent;"
            "}"
            "QPushButton:hover{"
                "background:#404040;"
            "}"
            "QPushButton:pressed{"
                "background:#3A7CA5;"
            "}"
        )

        # Если пресеты не переданы или пусты, используем дефолтные:
        if not presets:
            presets = [
                ("1S",   1),    ("5S",   5),    ("10S",  10),   ("30S",  30),
                ("1M",  60),   ("5M",  300),   ("10M", 600),  ("30M", 1800),
                ("1H", 3600),  ("2H", 7200),  ("3H",10800),  ("5H", 18000),
            ]

        # ————————————————————————————————————————————————
        # Корневой лэйаут
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # ————————————————————————————————————————————————
        # Сетка кнопок с пресетами
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(4)
        for idx, (txt, sec) in enumerate(presets):
            btn = QtWidgets.QPushButton(txt)
            # При клике шлём сигнал с количеством секунд
            btn.clicked.connect(lambda _, s=sec: self.add_time.emit(s))
            row = idx // 3
            col = idx % 3
            grid.addWidget(btn, row, col)

        root.addLayout(grid)

        # ————————————————————————————————————————————————
        # Блок управления (▶/‖ и ↻)
        ctrl = QtWidgets.QHBoxLayout()
        ctrl.setSpacing(4)
        style = self.style()

        # Кнопка «Запустить/Пауза»
        self.btn_run = QtWidgets.QPushButton()
        self._set_run_icon(paused=True)
        self.btn_run.clicked.connect(self.start_pause.emit)
        self.btn_run.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        ctrl.addWidget(self.btn_run, 1)

        # Кнопка «Сброс»
        self.btn_reset = QtWidgets.QPushButton()
        self.btn_reset.setIcon(style.standardIcon(QStyle.SP_BrowserReload))
        self.btn_reset.clicked.connect(self.reset_signal.emit)
        self.btn_reset.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        ctrl.addWidget(self.btn_reset, 1)

        # Кнопка «Свои часы»
        self.btn_custom = QtWidgets.QPushButton("…")
        self.btn_custom.clicked.connect(self.custom_time.emit)
        self.btn_custom.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        ctrl.addWidget(self.btn_custom, 1)

        root.addLayout(ctrl)

    @log_exceptions
    # ————————————————————————————————————————————————
    def _set_run_icon(self, paused: bool):
        """
        Рисует белую иконку ▶ или ‖ в зависимости от состояния paused.
        """
        std_icon = self.style().standardIcon(
            QStyle.SP_MediaPlay if paused else QStyle.SP_MediaPause
        )
        pix = std_icon.pixmap(24, 24)

        # Перекрашиваем иконку в белый цвет
        colored = QPixmap(pix.size())
        colored.fill(QtCore.Qt.transparent)
        p = QPainter(colored)
        p.drawPixmap(0, 0, pix)
        p.setCompositionMode(QPainter.CompositionMode_SourceIn)
        p.fillRect(colored.rect(), QColor("white"))
        p.end()

        self.btn_run.setIcon(QIcon(colored))

    @log_exceptions
    def reflect_state(self, running: bool):
        """
        Вызывается извне, чтобы обновить иконку кнопки Run/Pause.
        Если running == True → показываем «Пауза», иначе → «Play».
        """
        self._set_run_icon(paused=not running)
