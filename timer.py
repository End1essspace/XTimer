from utils import load_presets
import sys, time, math, ctypes, os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPainter, QPixmap, QColor, QIcon, QFontDatabase, QDesktopServices, QIcon
from PyQt5.QtWidgets import QStyle, QSizePolicy, QSystemTrayIcon, QMenu, QAction, QApplication
from PyQt5.QtCore import QPropertyAnimation, QAbstractAnimation, QRect, Qt, QTimer, QUrl
from PyQt5.QtMultimedia import QSound
from winapi import (
    taskbar_rect_edge, SetWindowPos, HWND_TOPMOST,
    SWP_NOMOVE, SWP_NOSIZE, SWP_NOACTIVATE,
    GetSM, GetFG, GetRect, RECT,
    SM_CXSCREEN, SM_CYSCREEN,
    HWND_NOTOPMOST,
)
from dialogs import SettingsDialog
from menu    import TimerMenu
from constants import SETTINGS_ICON, TRAY_ICON
from logging_config import log_exceptions
from update_checker import UpdateChecker
import logging

class TaskbarTimer(QtWidgets.QMainWindow):
    MIN_LEN, WIDTH_RATIO = 70, 0.09
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        icon_path = SETTINGS_ICON
        self.setWindowIcon(QIcon(icon_path))
        
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )
        app = QtWidgets.QApplication.instance()
        app.applicationStateChanged.connect(
            lambda _state: QtCore.QTimer.singleShot(0, self._force_topmost)
        )
        self._base_style = ""
        self._always_on_top = False
        # — состояние таймера —
        self.duration   = 0.0
        self.start_time = 0.0
        self.elapsed    = 0.0
        self.running    = False

        self.time_font_family = "Arial"
        # Размер шрифта (по умолчанию)
        self.time_font_size   = 12
        self._count_direction = "up"
        
        # — параметры «мигания» по завершении —
        self.blink_min_width    = 2
        self.blink_max_width    = 8
        self.blink_start_time   = None
        self.blink_pulse_freq   = 2.0     # Гц
        self.blink_border_width = 2

        # — экран, ориентация, размеры —
        self.sw, self.sh = GetSM(SM_CXSCREEN), GetSM(SM_CYSCREEN)
        self.orientation = "horizontal"   # или vertical / top / bottom / left / right
        self.snap_side   = None           # текущая «прилипшая» грань
        self.W = self.H = self._hW = self._hH = 0

        # — вспомогательные окна —
        self.dialog = None
        self.menu   = None

        # — drag’n’drop —
        self._drag = False
        self._off  = QtCore.QPoint()

        # начальная позиция
        self._place_horizontal()
        self._snap_and_orient()

        # — два QTimer’а: UI (~30 FPS) и логика (~5 FPS) —
        # внутри TaskbarTimer.__init__:
        self._ui_timer    = QtCore.QTimer(self, timeout=self.update)
        self._ui_timer.start(33)   # ~30 FPS для перерисовки (метод paintEvent)
        self._logic_timer = QtCore.QTimer(self, timeout=self._tick)
        self._logic_timer.start(26) # ~5 FPS для логики таймера (__tick)
        
        self._stay_top_timer = QtCore.QTimer(self, timeout=self._force_topmost)
        # интервал, который вам нужен
        self._stay_top_timer.setInterval(3000) 

        # кэш метрики tightBoundingRect для текста времени
        self._prev_label  = ""
        self._tight_cache = QtCore.QRect()
        logging.getLogger(__name__).debug("BASE_DIR     = %r", os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(__file__))
        logging.getLogger(__name__).debug("TRAY_ICON    = %r", TRAY_ICON)
        logging.getLogger(__name__).debug("Icon exists? = %s", os.path.exists(TRAY_ICON))
        logging.getLogger(__name__).debug("Tray avail?  = %s", QSystemTrayIcon.isSystemTrayAvailable())

        icon = QIcon(TRAY_ICON)
        logging.getLogger(__name__).debug("Icon isNull? = %s", icon.isNull())
        # ─── создаём иконку в системном трее ───
        self.tray = QtWidgets.QSystemTrayIcon(QtGui.QIcon(TRAY_ICON), self)
        self.tray.setToolTip("XTimer")
        self.tray.activated.connect(
            lambda reason: self.showNormal() if reason == QSystemTrayIcon.Trigger else None
        )
        self.tray.show()
        self.tray.setVisible(True)
        # 2. Формируем контекстное меню (ПКМ)
        tray_menu = QMenu(self)
        tray_menu.setStyleSheet("""
            QMenu {
                background-color: #333333;
                color: white;
            }
            QMenu::item:selected {
                background-color: #555555;
            }
        """)

        # Пункт «Показать/Скрыть окно»
        toggle_action = QAction("Показать/Скрыть окно", self)
        toggle_action.triggered.connect(
            lambda: QtCore.QTimer.singleShot(0, self._toggle_visibility)
        )
        tray_menu.addAction(toggle_action)

        # Разделитель
        tray_menu.addSeparator()

        # Пункт «Настройки»
        settings_action = QAction("Настройки", self)
        settings_action.triggered.connect(self._open_settings)
        tray_menu.addAction(settings_action)
        # Разделитель
        tray_menu.addSeparator()

        # Пункт «Выход»
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(QtWidgets.QApplication.quit)
        tray_menu.addAction(exit_action)

        self.tray.setContextMenu(tray_menu)
        self.tray.show()
        self.tray.setVisible(True)
        
        self._update_checker = UpdateChecker(self)
        self._update_checker.update_downloaded.connect(self._on_server_update)
        self._update_checker.update_available.connect(self._on_github_update)
        self._update_checker.update_failed.connect(self._on_update_failed)
        self.tray.messageClicked.connect(self._on_update_click)
        
        self._hide_from_taskbar()
        self.apply_settings()
        self.show()
        QtWidgets.QApplication.instance().applicationStateChanged.connect(
            lambda _state: QtCore.QTimer.singleShot(0, self._force_topmost)
        )
        self._stay_top_timer = QtCore.QTimer(self, timeout=self._force_topmost)
        self._stay_top_timer.start(3000)
    
    def _toggle_visibility(self) -> None:
        """
        • Если таймер полностью видим и НЕ свёрнут → прячем (`hide`).
        • В остальных случаях → показываем, раскручиваем из minimize,
        поднимаем поверх и снова делаем topmost.
        """
        minimized = bool(self.windowState() & QtCore.Qt.WindowMinimized)
        fully_visible = self.isVisible() and not minimized

        if fully_visible:
            self.hide()
            return

        # снимаем флаг Minimized, если он есть
        if minimized:
            self.setWindowState(self.windowState() & ~QtCore.Qt.WindowMinimized)

        self.show()          # делает видимым
        self.raise_()        # поверх других окон
        self.activateWindow()
        self._force_topmost()
        
    def _open_settings(self):
        # если уже открыто – поднимаем
        if hasattr(self, "settings_dialog") and self.settings_dialog.isVisible():
            self.settings_dialog.raise_()
            return

        # СОЗДАЁМ БЕЗ РОДИТЕЛЯ  ↓
        self.settings_dialog = SettingsDialog()

        # подписываемся на сигнал
        self.settings_dialog.settings_changed.connect(self.apply_settings)

        self.settings_dialog.check_updates.connect(self._do_autoupdate)

        # чтобы обновить статус кнопки в диалоге по результатам
        self._update_checker.update_available.connect(
            lambda tag, url: self.settings_dialog.lbl_update_status.setText(f"Найдена версия {tag}")
        )
        self._update_checker.update_downloaded.connect(
            lambda _:        self.settings_dialog.lbl_update_status.setText("Обновление установлено")
        )
        self._update_checker.update_failed.connect(
            lambda stage:    self.settings_dialog.lbl_update_status.setText(f"Ошибка: {stage} и сервер проекта недоступен")
        )
        # позиционируем (центр экрана)
        self._position_dialog(self.settings_dialog)

        self.settings_dialog.show()



    def apply_settings(self):
        settings = QtCore.QSettings("MyCompany", "TaskbarTimer")

        # 1) чекбокс «Всегда поверх окон»
        always_on_top = settings.value("timer/always_on_top", False, type=bool)
        self._always_on_top = always_on_top         # ← запоминаем

        # запустить / остановить сторож-таймер
        if always_on_top:
            if not self._stay_top_timer.isActive():
                self._stay_top_timer.start()
        else:
            self._stay_top_timer.stop()

        # применяем флаги окна (без show!)
        self._apply_window_flags(always_on_top)

        # ↓ один вызов, чтобы сразу выставить нужный уровень TOPMOST/NOTOPMOST
        self._force_topmost()

        # 2) Флаг «Сворачивать в трей при старте»
        self.minimize_to_tray = settings.value("timer/minimize_to_tray", False, type=bool)
        if self.minimize_to_tray:
            self.hide()
        else:
            self.show()
            
        # 3) Флаг «Автостарт при добавлении времени»
        self.auto_start_on_add = settings.value("timer/auto_start", False, type=bool)

        self._count_direction = QtCore.QSettings("MyCompany", "TaskbarTimer") \
            .value("timer/count_direction", "up", type=str)

        # === Внешний вид ===

        # 4) Тема: «system», «light» или «dark»
        theme = settings.value("appearance/theme", "dark")
        self._theme = theme
        if theme == "dark":
            # устанавливаем только фон окна таймера (белая рамка/текст будет рисоваться вручную в paintEvent)
            self.setStyleSheet(self._base_style + "background:#202020;")
        elif theme == "light":
            self.setStyleSheet(self._base_style + "background:#FFFFFF;")

        # 5) Цвет прогресс-бара (он остаётся без изменений)
        color = settings.value("appearance/progress_color", "#55FF55")
        self.progress_color = QtGui.QColor(color)
        
        font_family = settings.value("appearance/font", self.time_font_family, type=str)
        if font_family:
            self.time_font_family = font_family
        # ... и далее остальные настройки (звук, пресеты и т.д.) ...
        font_family = settings.value("appearance/font", self.time_font_family, type=str)
        font_size   = settings.value("appearance/font_size", self.time_font_size, type=int)
        if font_family:
            self.time_font_family = font_family
        if font_size:
            self.time_font_size = font_size

        # === Оповещения ===

        # 6) Включён ли звук при окончании
        self.sound_enabled = settings.value("alerts/sound_enabled", False, type=bool)

        # 7) Путь к файлу звука
        self.sound_file = settings.value("alerts/sound_file", "", type=str)

        # 8) Включено ли мигание рамки при окончании
        self.blink_enabled = settings.value("alerts/blink_enabled", False, type=bool)

        if not self.blink_enabled:
            self.blink_start_time = None
        # 9) Частота мигания (в герцах)
        self.blink_pulse_freq = settings.value("alerts/blink_freq", 2.0, type=float)

        # === Пресеты кнопок быстрого добавления времени ===

        presets = load_presets()

        # Пересоздаём TimerMenu с новыми пресетами
        if hasattr(self, "menu") and self.menu:
            self.menu.close()
            self.menu.deleteLater()
            self.menu = None

        self.menu = TimerMenu(self, presets=presets)
        self.menu.add_time.connect(self._add_duration)
        self.menu.start_pause.connect(self._toggle_start_pause)
        self.menu.reset_signal.connect(self._reset_timer)
        self.menu.custom_time.connect(self._open_dialog)

        # === Автообновление ===

        # 12) Флаг «Включить автообновление»
        autoupd = settings.value("general/auto_update_enabled", False, type=bool)

        # 13) Интервал проверки (в минутах)
        interval = settings.value("general/update_interval", 10080, type=int)
    
        if autoupd:
            if not hasattr(self, "_autoupd_timer"):
                self._autoupd_timer = QtCore.QTimer(self)
                self._autoupd_timer.timeout.connect(self._do_autoupdate)
            self._autoupd_timer.start(interval * 60 * 1000)
        else:
            if hasattr(self, "_autoupd_timer"):
                self._autoupd_timer.stop()

        
    def on_tray_icon_activated(self, reason):
        """
        Обработка кликов по иконке.
        QSystemTrayIcon.Trigger — обычный клик ЛКМ
        QSystemTrayIcon.Context — ПКМ (контекстное меню обрабатывается автоматически)
        """
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()
    # ──────────────────────────────────────────────────────────────
    #  вспомогательные расчёты ориентации / размера
    # ──────────────────────────────────────────────────────────────
    def _snap_and_orient(self):
        """
        Находит ближайшую грань экрана; если таймер уже «в углу»,
        ориентацию не меняет.
        """
        self.sw, self.sh = GetSM(0), GetSM(1)
        geo  = self.geometry()
        dists = {
            "left":   abs(geo.left()),
            "right":  abs(self.sw - geo.right()),
            "top":    abs(geo.top()),
            "bottom": abs(self.sh - geo.bottom()),
        }
        min_val   = min(dists.values())
        min_sides = [s for s, v in dists.items() if v == min_val]
        if len(min_sides) > 1:  # угол — оставляем прежнее
            return
        side = min_sides[0]
        self.snap_side   = side
        self.orientation = "horizontal" if side in ("top", "bottom") else "vertical"

    def _place_horizontal(self):
        """
        Ставит таймер *над* панелью задач (если она снизу)
        или *под* панелью (если она сверху).  При вертикальной
        панели остаётся в её центре (как раньше).

        ─ edge: 0=left, 1=top, 2=right, 3=bottom
        """
        rc, edge = taskbar_rect_edge()
        tbw, tbh = rc.right - rc.left, rc.bottom - rc.top

        H = tbh // 2                             # высота таймера = половина taskbar
        W = max(self.MIN_LEN, int(tbw * self.WIDTH_RATIO))

        self.W, self._hW = W, W
        self.H, self._hH = H, H

        xc = rc.left + (tbw - W) // 2            # центр-по-горизонтали
        gap = 4                                  # небольшой отступ от панели

        if edge == 3:          # taskbar снизу → таймер над ним
            x = xc
            y = rc.top - H - gap
        elif edge == 1:        # taskbar сверху → таймер под ним
            x = xc
            y = rc.bottom + gap
        else:                  # taskbar слева / справа → прежняя логика (в центре панели)
            x = xc
            y = rc.top + (tbh - H) // 2

        self.setGeometry(x, y, W, H)
        self._force_topmost()


    def _snap(self, side: str, vertical: bool):
        """
        «Прилипает» к указанной грани экрана и,
        при необходимости, меняет ориентацию.
        """
        if vertical:
            self.W, self.H = self._hH, self._hW
        else:
            self.W, self.H = self._hW, self._hH

        if vertical:
            x = 0 if side == "left" else self.sw - self.W
            y = max(0, min(self.y(), self.sh - self.H))
        else:
            y = 0 if side == "top" else self.sh - self.H
            x = max(0, min(self.x(), self.sw - self.W))

        self.orientation = self.snap_side = side
        self.setGeometry(x, y, self.W, self.H)
        self._force_topmost()
        self._close_menu()

    def _force_topmost(self):
        """Поднимает или опускает окно в TOPMOST-группе по флагу self._always_on_top."""
        hwnd = int(self.winId())
        always = getattr(self, "_always_on_top", False)  # подстраховка, если атрибут ещё не создан
        insert_after = HWND_TOPMOST if always else HWND_NOTOPMOST

        SetWindowPos(
            hwnd,
            insert_after,
            0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
        )

    def _apply_window_flags(self, always_on_top: bool) -> None:
        """
        Настраивает флаги окна:
        – Frameless + Qt.Tool всегда;
        – + WindowStaysOnTopHint, если always_on_top=True.
        """
        # 1) Собираем нужный набор флагов
        flags = QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool
        if always_on_top:
            flags |= QtCore.Qt.WindowStaysOnTopHint

        # 2) Перевыставляем их
        self.setWindowFlags(flags)

        # 3) Поднимаем окно в нужную группу (TOPMOST/NOTOPMOST)
        self._force_topmost()
    
    def _hide_from_taskbar(self):
        if sys.platform.startswith("win"):
            hwnd           = int(self.winId())          # дескриптор окна
            GWL_EXSTYLE    = -20
            WS_EX_APPWINDOW= 0x00040000
            WS_EX_TOOLWINDOW=0x00000080

            user32  = ctypes.windll.user32
            style   = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style   = (style & ~WS_EX_APPWINDOW) | WS_EX_TOOLWINDOW
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

    # ──────────────────────────────────────────────────────────────
    #  меню  +  диалог
    # ──────────────────────────────────────────────────────────────
    def _open_menu(self):
        """
        Открываем меню с кнопками добавления времени.
        Берём список пресетов из QSettings (как в apply_settings()).
        """
        presets = load_presets()

        # Пересоздаём меню
        if hasattr(self, "menu") and self.menu:
            self.menu.close()
            self.menu.deleteLater()
            self.menu = None

        self.menu = TimerMenu(self, presets=presets)

        # -------------- ЭТОТ БЛОК ЗАМЕНИТЕ --------------
        if self.orientation in ("horizontal", "top", "bottom"):
            # таймер широкий → меню такой же ширины
            self.menu.setFixedWidth(self.width())
        else:
            # таймер узкий вертикальный → «натуральная» ширина меню
            self.menu.adjustSize()
        # затем в любом случае:
        self._position_menu()

        # сигналы – без изменений
        self.menu.add_time.connect(self._add_duration)
        self.menu.start_pause.connect(self._toggle_start_pause)
        self.menu.reset_signal.connect(self._reset_timer)
        self.menu.custom_time.connect(self._open_settings)
        
        self.menu.reflect_state(self.running)

        self.menu.setWindowOpacity(0.0)
        self.menu.show()
        anim = QPropertyAnimation(self.menu, b"windowOpacity", self)
        anim.setDuration(200)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QtCore.QEasingCurve.InOutQuad)
        anim.start(QAbstractAnimation.DeleteWhenStopped)

    # обязательно после show() !
        self._position_menu()
        
    def _close_menu(self):
        if not (self.menu and self.menu.isVisible()):
            return
        anim = QPropertyAnimation(self.menu, b"windowOpacity", self)
        anim.setDuration(200)
        anim.setStartValue(self.menu.windowOpacity())
        anim.setEndValue(0.0)
        anim.setEasingCurve(QtCore.QEasingCurve.InOutQuad)
        anim.finished.connect(self.menu.close)
        anim.start(QAbstractAnimation.DeleteWhenStopped)

    # timer.py  ─ метод _position_menu --------------------------------
    # файл: timer.py  ── метод _position_menu
    # файл: timer.py  ── метод _position_menu
    # файл: timer.py ── метод _position_menu
    # файл: timer.py ── метод _position_menu
    def _position_menu(self):
        if not self.menu:
            return

        # 1) размеры меню
        mw, mh = self.menu.sizeHint().width(), self.menu.sizeHint().height()
        # 2) геометрия всего экрана (для проверки границ)
        scr    = QtWidgets.QApplication.primaryScreen().geometry()
        # 3) прямоугольник нашего таймера (где он сейчас стоит)
        timer  = QtCore.QRect(self.x(), self.y(), self.width(), self.height())

        # ───────── ГОРИЗОНТАЛЬНЫЙ ТАЙМЕР ─────────
        if self.orientation in ("horizontal", "top", "bottom"):
            # a) сначала пытаемся поставить меню над таймером
            y = timer.top() - mh - 4
            # если не влезает сверху → показываем снизу
            if y < scr.top():
                y = timer.bottom() + 4

            # b) по горизонтали центрируем относительно таймера, но не выходим за экран
            x = max(scr.left(), min(timer.left(), scr.right() - mw))

            # c) перемещаем меню и поднимаем его над всеми
            self.menu.move(x, y)
            self.menu.raise_()
            return

        # ───────── ВЕРТИКАЛЬНЫЙ ТАЙМЕР ─────────
        else:  
            x_left = timer.left() - mw - 4
            
            if x_left >= scr.left():
                x = x_left - 48
            else:
                x_right = timer.right() + 4
            
                if x_right + mw <= scr.right():
                    x = x_right
                else:
                    x = x_left

            
            # b) по вертикали центрируем меню относительно таймера, но не выходим за экран
            y = timer.top() + (timer.height() - mh) // 2
            y = max(scr.top(), min(y, scr.bottom() - mh))

            # c) перемещаем меню и поднимаем его над всеми
            self.menu.move(x, y)
            self.menu.raise_()
            return


    def _open_dialog(self):
        self._position_dialog(self.dialog)
        self.dialog.accepted.connect(self._set_duration)
        self.dialog.show()

    def _position_dialog(self, child):
        """
        Универсальный метод для позиционирования дочернего окна `child`
        (TimeDialog или SettingsDialog) рядом с главным таймером.
        """
        # 1) если это окно настроек – центрируем по экрану
        from dialogs import SettingsDialog
        if isinstance(child, SettingsDialog):
            scr = QtWidgets.QApplication.primaryScreen().geometry()
            dw  = child.sizeHint().width()
            dh  = child.sizeHint().height()
            cx  = scr.x() + (scr.width()  - dw) // 2
            cy  = scr.y() + (scr.height() - dh) // 2
            child.move(cx, cy)
            return

        # 2) иначе – старая логика: рядом с таймером (как было раньше)
        dw = child.sizeHint().width()
        dh = child.sizeHint().height()
        scr = QtWidgets.QApplication.primaryScreen().geometry()

        # позиционируем справа от главного окна, с отступом 10px
        x = self.x() + self.width() + 10
        y = self.y() + (self.height() - dh) // 2

        # если не помещается справа → ставим слева
        if x + dw > scr.x() + scr.width():
            x = self.x() - dw - 10

        # если не помещается ни слева, ни справа → привязываем к центру таймера
        if x < scr.x() or x + dw > scr.x() + scr.width():
            x = self.x() + (self.width() - dw) // 2
        if y < scr.y():
            y = scr.y() + 10
        elif y + dh > scr.y() + scr.height():
            y = scr.y() + scr.height() - dh - 10

        child.move(x, y)


    # ──────────────────────────────────────────────────────────────
    #  обработка мыши
    # ──────────────────────────────────────────────────────────────
    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.LeftButton:
            self._drag = True
            self._off  = e.globalPos() - self.frameGeometry().topLeft()
            self.snap_side = None
        elif e.button() == QtCore.Qt.RightButton:
            if self.menu and self.menu.isVisible():
                self._close_menu()
            else:
                self._open_menu()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if not self._drag:
            super().mouseMoveEvent(e)
            return
        pos = e.globalPos() - self._off
        x   = max(0, min(pos.x(), self.sw - self.W))
        y   = max(0, min(pos.y(), self.sh - self.H))
        self.move(x, y)
        self._force_topmost()

        # определяем касание граней
        touches = [x <= 0, x + self.W >= self.sw, y <= 0, y + self.H >= self.sh]
        c = touches.count(True)
        if c == 0:
            self.snap_side = None
        elif c == 1 and self.snap_side is None:
            if touches[0]:
                self._snap("left",  True)
            elif touches[1]:
                self._snap("right", True)
            elif touches[2]:
                self._snap("top",   False)
            else:
                self._snap("bottom", False)

        if self.menu and self.menu.isVisible():
            self._position_menu()

        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == QtCore.Qt.LeftButton:
            self._drag = False
        super().mouseReleaseEvent(e)
    
    def hideEvent(self, event: QtGui.QHideEvent) -> None:
        # При скрытии окна останавливаем только UI-таймер
        self._ui_timer.stop()
        super().hideEvent(event)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        # При показе – снова запускаем UI-таймер (~30 FPS)
        self._ui_timer.start(33)
        super().showEvent(event)
    # ──────────────────────────────────────────────────────────────
    #  управление временем
    # ──────────────────────────────────────────────────────────────
    @log_exceptions
    def _add_duration(self, secs: int):
        self.duration += secs
        self.blink_start_time = None

        if self.auto_start_on_add:
            if not self.running:
                self._toggle_start_pause()
        # Если авто-старт выключен — добавление времени должно ставить таймер на паузу (только если он запущен)
        else:
            if self.running:
                self._toggle_start_pause()

        if self.menu:
            self.menu.reflect_state(self.running)

        self.update()


    def _set_duration(self, secs: int):
        self.duration = secs
        self.elapsed  = 0.0
        self.running  = False
        self.blink_start_time = None
        self.update()

    def _toggle_start_pause(self):
        if not self.duration:
            return
        if not self.running:
            self.start_time = time.monotonic() - self.elapsed
            self.running    = True
        else:
            self.running    = False
        if self.menu:
            self.menu.reflect_state(self.running)
        if self.running and getattr(self, "minimize_to_tray", False):
            self.hide()
                
    @log_exceptions
    def _reset_timer(self):
        self.duration = self.elapsed = 0.0
        self.running  = False
        self.blink_start_time = None
        self.update()
        if self.menu:
            self.menu.reflect_state(self.running)

    # ──────────────────────────────────────────────────────────────
    #  «тик» логики и перерисовка
    # ──────────────────────────────────────────────────────────────
    @log_exceptions
    def _tick(self):
        # … (логика скрытия/показа окна в зависимости от фуллскрина) …
        if self.running:
            self.elapsed = min(time.monotonic() - self.start_time, self.duration)
            if self.elapsed >= self.duration:
                # проигрываем звук при окончании, если включено
                if self.sound_enabled and self.sound_file:
                    if os.path.isfile(self.sound_file):
                        ext = os.path.splitext(self.sound_file)[1].lower()
                        if ext == ".wav":
                            QSound.play(self.sound_file)
                        else:
                            logging.getLogger(__name__).warning(
                                "Неподдерживаемый формат звука %s — используйте WAV", self.sound_file
                            )
                    else:
                        logging.getLogger(__name__).warning(
                            "Звуковой файл не найден: %s", self.sound_file
                        )

                self.running = False
                # Запускаем мигание только если пользователь включил его в настройках
                if self.blink_enabled:
                    self.blink_start_time = time.monotonic()
                if self.menu:
                    self.menu.reflect_state(self.running)

        self.update()
        
    @log_exceptions
    def _do_autoupdate(self):
        """Вызывается по таймеру — стартуем full-check."""
        self._update_checker.check_for_update()

    def _on_server_update(self, app_dir: str):
        """Обновление с сервера установлено — перезапускаем приложение."""
        self.tray.showMessage("XTimer", "Обновление с сервера установлено. Перезапуск через 2s...", QSystemTrayIcon.Information, 5000)
        QTimer.singleShot(2000, lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(sys.argv[0])))

    def _on_github_update(self, tag: str, url: str):
        """Найден новый релиз на GitHub — показываем ссылку."""
        self._update_url = url
        self.tray.showMessage("XTimer", f"Новая версия {tag} доступна. Кликните для скачивания.", QSystemTrayIcon.Information, 10000)

    def _on_update_failed(self, stage: str):
        logger = logging.getLogger(__name__)
        logger.warning(f"Auto-update failed at stage: {stage}")

    def _on_update_click(self):
        """По клику открываем страницу релиза, если есть URL."""
        if hasattr(self, "_update_url"):
            QDesktopServices.openUrl(QUrl(self._update_url))

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # 1) Рамка (мигание по завершении, если включено)
        if self.blink_enabled and self.blink_start_time is not None:
            t     = time.monotonic() - self.blink_start_time
            alpha = int(((math.sin(2 * math.pi * self.blink_pulse_freq * t) + 1) / 2) * 255)
            bw    = self.blink_border_width
        else:
            bw    = 2
            alpha = 255

        # Цвет рамки по теме
        if getattr(self, "_theme", "dark") == "light":
            border_color = QColor(0, 0, 0, alpha)       # чёрная рамка в светлой теме
        else:
            border_color = QColor(255, 255, 255, alpha) # белая рамка в тёмной теме

        pen = QtGui.QPen(border_color, bw)
        p.setPen(pen)
        half = bw // 2
        p.drawRect(half, half, self.W - bw, self.H - bw)

        # 2) Прогресс-бар
        dur = float(self.duration) if self.duration else 0.0
        el  = min(float(self.elapsed), dur) if dur else 0.0
        ratio_elapsed = (el / dur) if dur else 0.0

        # для "down" хотим показывать остаток → бар «усыхает»
        is_down = (getattr(self, "_count_direction", "up") == "down")
        ratio   = (1.0 - ratio_elapsed) if is_down else ratio_elapsed

        brush = QtGui.QBrush(self.progress_color)

        if self.orientation in ("horizontal", "top", "bottom"):
            # горизонталь: всегда рисуем слева направо,
            # но при "down" ширина уменьшается к нулю
            fill_w = int((self.W - bw - 2) * ratio)
            if fill_w > 0:
                p.fillRect(
                    half + 1,
                    half + 1,
                    fill_w,
                    self.H - bw - 2,
                    brush,
                )
        else:
            # вертикаль:
            # при "up" заполняем снизу вверх (как было),
            # при "down" — сверху вниз (усыхает к нулю).
            if is_down:
                fill_h = int((self.H - bw - 2) * ratio)  # остаток
                if fill_h > 0:
                    p.fillRect(
                        half + 1,
                        half + 1,
                        self.W - bw - 2,
                        fill_h,
                        brush,
                    )
            else:
                fill_h = int((self.H - bw - 2) * ratio_elapsed)
                if fill_h > 0:
                    p.fillRect(
                        half + 1,
                        self.H - half - 1 - fill_h,
                        self.W - bw - 2,
                        fill_h,
                        brush,
                    )

        # 3) Текст «HH:MM:SS»
        # up: показываем прошедшее; down: показываем оставшееся
        if is_down:
            total = max(dur - el, 0.0)
        else:
            total = el if (self.running or el) else dur

        hh, rem = divmod(int(total), 3600)
        mm, ss  = divmod(rem, 60)
        label   = f"{hh:02d}:{mm:02d}:{ss:02d}"

        # 4) Шрифт пользователя
        font = QtGui.QFont(self.time_font_family, self.time_font_size, QtGui.QFont.Bold)
        p.setFont(font)

        # 5) Прямоугольник рисования текста
        rect = self.rect()  # QRect(0, 0, self.W, self.H)

        # 6) Рисуем текст с обводкой (по теме)
        if self.orientation in ("horizontal", "top", "bottom"):
            if getattr(self, "_theme", "dark") == "light":
                p.setPen(QtGui.QPen(QColor(255, 255, 255), 3))
                p.drawText(rect, Qt.AlignCenter, label)
                p.setPen(QtGui.QPen(QColor(0, 0, 0), 1))
                p.drawText(rect, Qt.AlignCenter, label)
            else:
                p.setPen(QtGui.QPen(QColor(0, 0, 0), 3))
                p.drawText(rect, Qt.AlignCenter, label)
                p.setPen(QtGui.QPen(QColor(255, 255, 255), 1))
                p.drawText(rect, Qt.AlignCenter, label)
        else:
            # вертикальный режим (поворот текста)
            p.save()
            p.translate(self.W / 2, self.H / 2)
            p.rotate(-90)
            rect_rotated = QtCore.QRectF(-self.H / 2, -self.W / 2, self.H, self.W)

            if getattr(self, "_theme", "dark") == "light":
                p.setPen(QtGui.QPen(QColor(255, 255, 255), 3))
                p.drawText(rect_rotated, Qt.AlignCenter, label)
                p.setPen(QtGui.QPen(QColor(0, 0, 0), 1))
                p.drawText(rect_rotated, Qt.AlignCenter, label)
            else:
                p.setPen(QtGui.QPen(QColor(0, 0, 0), 3))
                p.drawText(rect_rotated, Qt.AlignCenter, label)
                p.setPen(QtGui.QPen(QColor(255, 255, 255), 1))
                p.drawText(rect_rotated, Qt.AlignCenter, label)
            p.restore()

        p.end()


