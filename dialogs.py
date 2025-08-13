# dialogs.py
import os
from PyQt5 import QtCore, QtWidgets, QtGui
from utils import load_raw_presets, save_presets
from constants import SETTINGS_ICON
from logging_config import log_exceptions

class SettingsDialog(QtWidgets.QWidget):
    """
    Окно настроек для XTimer.
    Содержит вкладки: Общие, Внешний вид, Поведение, Оповещения и Пресеты.
    При нажатии Apply/OK эмитит сигнал settings_changed().
    """
    settings_changed = QtCore.pyqtSignal()
    check_updates    = QtCore.pyqtSignal()
    
    def __init__(self):
        super().__init__(
            None,
            QtCore.Qt.Window                      # обычное окно
            | QtCore.Qt.WindowMinimizeButtonHint  # кнопка “─”
            | QtCore.Qt.WindowCloseButtonHint     # кнопка “×”
        )
        self.setWindowTitle("Настройки XTimer")
        self.setWindowTitle("Настройки XTimer")
        icon_path = SETTINGS_ICON
        self.setWindowIcon(QtGui.QIcon(icon_path))
        self.setMinimumSize(500, 450)
        self.setMaximumSize(700, 600)

        # — GLOBAL STYLE SHEET (Light Theme) —
        # ... внутри __init__(...)
        self.setStyleSheet("""
            /* ─────────────────────  Глобально  ───────────────────── */
            QWidget {
                background-color: #FFFFFF;
                color: #2B2B2B;
            }

            /* ─────────── QTabWidget / QTabBar ─────────── */
            QTabWidget::pane {
                border: 1px solid #4B8BBE;
                padding: 5px;
                background: #FFFFFF;
            }
            QTabBar::tab {
                background: #F0F0F0;
                color: #2B2B2B;
                padding: 8px 16px;
                border: 1px solid #4B8BBE;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
                min-width: 80px;
            }
            QTabBar::tab:selected { background: #FFFFFF; }
            QTabBar::tab:hover    { background: #D0E4F7; }

            /* ─────────── Текст / чекбоксы ─────────── */
            QLabel, QCheckBox, QRadioButton {
                font-size: 10pt;
                color: #2B2B2B;
            }
            QCheckBox::indicator:unchecked {
                width: 14px; height: 14px;
                border: 1px solid #2B2B2B;
                border-radius: 2px;
                background: transparent;
            }
            QCheckBox::indicator:checked {
                width: 14px; height: 14px;
                border-radius: 2px;
                background: #4B8BBE;
                border: 1px solid #4B8BBE;
            }

            /* ─────────── LineEdit / ComboBox ─────────── */
            QLineEdit, QComboBox {
                background: #FFFFFF;
                color: #2B2B2B;
                border: 1px solid #4B8BBE;
                border-radius: 4px;
                padding: 4px;
            }
            QComboBox QAbstractItemView {
                background: #FFFFFF;
                color: #2B2B2B;
                selection-background-color: #D3D8DE;
            }

            /* ─────────────────── QSpinBox ─────────────────── */
            QSpinBox {
                background: #FFFFFF;
                color: #2B2B2B;
                border: 1px solid #4B8BBE;
                border-radius: 4px;
                padding: 2px 4px 2px 4px;        /* немного места слева от текста */
            }

            /* ─────────── Кнопки Apply / OK / Cancel ─────────── */
            QPushButton {
                background: #4B8BBE;
                color: #FFFFFF;
                border: none;
                padding: 6px 35px;
                border-radius: 4px;
                min-height: 28px;
            }
            QPushButton:hover   { background: #6EA9D1; }
            QPushButton:pressed { background: #346E8A; }
            QPushButton#btn_apply,
            QPushButton#btn_ok,
            QPushButton#btn_cancel { min-width: 75px; }

            /* ─────────── QTableWidget (Пресеты) ─────────── */
            QTableWidget {
                background: #FFFFFF;
                color: #2B2B2B;
                border: 1px solid #4B8BBE;
                border-radius: 4px;
                gridline-color: #4B8BBE;
            }
            QHeaderView::section {
                background: #4B8BBE;
                color: #FFFFFF;
                padding: 4px;
                border: 1px solid #4B8BBE;
            }
            QTableWidget::item:selected {
                background: #D0E4F7;
                color: #2B2B2B;
            }
            QPushButton#btn_pick_color {
                padding: 0px;             /* убираем отступы */
                border: 1px solid #D0E4F7;/* хотите ещё тоньше – поставьте 0.5px */
                border-radius: 4px;       /* можно чуть скруглить края */
                min-width: 64px;          /* чтобы по высоте/ширине не схлопнулась */
            }
        """)

        # Единый шрифт для окна настроек
        font = QtGui.QFont("Segoe UI", 10)
        self.setFont(font)

        # Загрузка текущих настроек
        settings = QtCore.QSettings("MyCompany", "TaskbarTimer")
        self._theme = settings.value("appearance/theme", "dark", type=str) or "dark"
        color_name = settings.value("appearance/progress_color", "#55FF55", type=str)
        self._progress_color = QtGui.QColor(color_name)

        # Основной лэйаут
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # Вкладки
        self.tabs = QtWidgets.QTabWidget(self)
        main_layout.addWidget(self.tabs)

        # === Вкладка “Общие” ===
        self._create_general_tab()

        # === Вкладка “Внешний вид” ===
        self._create_appearance_tab()

        # === Вкладка “Поведение” ===
        self._create_behavior_tab()
        
        self.btn_check_updates.clicked.connect(self._on_check_updates)
        # === Вкладка “Оповещения” ===
        self._create_alerts_tab()
        
        # === Вкладка “Пресеты” ===
        self._create_presets_tab()

        # Кнопки Apply, OK, Cancel
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch(1)
        self.btn_apply = QtWidgets.QPushButton("Apply")
        self.btn_ok    = QtWidgets.QPushButton("OK")
        self.btn_cancel= QtWidgets.QPushButton("Cancel")
        self.btn_apply.setObjectName("btn_apply")
        self.btn_ok.setObjectName("btn_ok")
        self.btn_cancel.setObjectName("btn_cancel")
        btn_layout.addWidget(self.btn_apply)
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        main_layout.addLayout(btn_layout)

        # Сигналы кнопок
        self.btn_apply.clicked.connect(self._on_apply_clicked)
        self.btn_ok.clicked.connect(self._on_ok_clicked)
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)

    def _create_general_tab(self):
        """
        Вкладка “Общие”: флаги «Всегда поверх», «Сворачивать в трей при старте», «Автостарт при добавлении времени»
        """
        general_tab = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(general_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        settings = QtCore.QSettings("MyCompany", "TaskbarTimer")

        # Чекбокс «Всегда поверх окон»
        self.chk_always_on_top = QtWidgets.QCheckBox("Всегда поверх окон")
        always_on_top = settings.value("timer/always_on_top", False, type=bool)
        self.chk_always_on_top.setChecked(always_on_top)
        layout.addRow(self.chk_always_on_top)

        # Чекбокс «Сворачивать в трей при старте»
        self.chk_minimize_to_tray = QtWidgets.QCheckBox("Сворачивать в трей при старте")
        minimize_to_tray = settings.value("timer/minimize_to_tray", False, type=bool)
        self.chk_minimize_to_tray.setChecked(minimize_to_tray)
        layout.addRow(self.chk_minimize_to_tray)

        # Чекбокс «Автостарт при добавлении времени»
        self.chk_auto_start = QtWidgets.QCheckBox("Автостарт при добавлении времени")
        auto_start = settings.value("timer/auto_start", False, type=bool)
        self.chk_auto_start.setChecked(auto_start)
        layout.addRow(self.chk_auto_start)

                # Комбо «Логика таймера»
        lbl_logic = QtWidgets.QLabel("Логика таймера:")
        self.combo_count_dir = QtWidgets.QComboBox()
        self.combo_count_dir.addItems(["По возрастанию", "По убыванию"])

        # читаем сохранённое значение ("up" | "down"), по умолчанию — up
        saved_dir = settings.value("timer/count_direction", "up", type=str)
        self.combo_count_dir.setCurrentIndex(0 if saved_dir == "up" else 1)

        layout.addRow(lbl_logic, self.combo_count_dir)
        
        self.tabs.addTab(general_tab, "Общие")

    def _create_appearance_tab(self):
        """
        Вкладка “Внешний вид”: выбор темы (для фона таймера) и цвет прогресс-бара
        """
        appearance_tab = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(appearance_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # Комбо-бокс «Тема»
        lbl_theme = QtWidgets.QLabel("Тема:")
        self.combo_theme = QtWidgets.QComboBox()
        self.combo_theme.addItems(["Тёмная", "Светлая"])
        if self._theme == "dark":
            self.combo_theme.setCurrentIndex(0)
        else:
            self.combo_theme.setCurrentIndex(1)
        self.combo_theme.currentIndexChanged.connect(self._on_theme_changed)
        layout.addRow(lbl_theme, self.combo_theme)
        

       # Читаем сохранённый шрифт или устанавливаем дефолт из TaskbarTimer
        settings = QtCore.QSettings("MyCompany", "TaskbarTimer")
       # Вместо self.time_font_family ставим вполне конкретный дефолт, например "Arial"
        saved_font = settings.value("appearance/font", "Arial", type=str)

        lbl_font = QtWidgets.QLabel("Шрифт:")
        self.font_combo = QtWidgets.QFontComboBox()
        # Устанавливаем текущий шрифт в комбобоксе
        if saved_font:
            # Поиск индекса сохранённого шрифта и установка
            idx = self.font_combo.findText(saved_font)
            if idx >= 0:
                self.font_combo.setCurrentIndex(idx)
        # Сохраняем свойство в экземпляр (чтобы позже при сохранении знать текущее значение)
        self._font = saved_font
        # При изменении выбора обновляем локальную переменную
        self.font_combo.currentFontChanged.connect(lambda f: setattr(self, "_font", f.family()))
        layout.addRow(lbl_font, self.font_combo)
        
        saved_size = settings.value("appearance/font_size", 12, type=int)
        lbl_size = QtWidgets.QLabel("Размер шрифта:")
        self.spin_font_size = QtWidgets.QSpinBox()
        self.spin_font_size.setRange(6, 22)  # допустимый диапазон: от 6 до 100 пунктов
        self.spin_font_size.setValue(saved_size)
        self._font_size = saved_size
        self.spin_font_size.valueChanged.connect(lambda v: setattr(self, "_font_size", v))
        layout.addRow(lbl_size, self.spin_font_size)
        
        # ————————————————————————————————————————————————————————————
        # Цвет прогресс-бара
        lbl_prog = QtWidgets.QLabel("Цвет прогресс-бара:")
        self.btn_pick_color = QtWidgets.QPushButton()
        self.btn_pick_color.setObjectName("btn_pick_color")
        self.btn_pick_color.setFixedWidth(80)
        self._update_color_button(self._progress_color)
        self.btn_pick_color.clicked.connect(self._on_pick_color)
        layout.addRow(lbl_prog, self.btn_pick_color)

        self.tabs.addTab(appearance_tab, "Внешний вид")

    def _create_behavior_tab(self):
        """
        Вкладка “Поведение”: настройки автопроверки, интервал обновлений
        """
        behavior_tab = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(behavior_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        settings = QtCore.QSettings("MyCompany", "TaskbarTimer")

        # Чекбокс «Автообновление»
        self.chk_auto_update = QtWidgets.QCheckBox("Включить автообновление")
        auto_update = settings.value("general/auto_update_enabled", False, type=bool)
        self.chk_auto_update.setChecked(auto_update)
        layout.addRow(self.chk_auto_update)

        # Поле «Интервал обновлений (мин)»
        lbl_interval = QtWidgets.QLabel("Интервал обновлений (мин):")
        self.spin_update_interval = QtWidgets.QSpinBox()
        self.spin_update_interval.setRange(1, 10080)  # от 1 минуты до дня
        raw_interval = settings.value("general/update_interval", None)
        try:
            interval = int(raw_interval) if raw_interval is not None else 60
        except (ValueError, TypeError):
            interval = 60
        self.spin_update_interval.setValue(interval)
        layout.addRow(lbl_interval, self.spin_update_interval)

        self.btn_check_updates = QtWidgets.QPushButton("Проверить обновления…")
        layout.addRow(self.btn_check_updates)
        # статус проверки
        self.lbl_update_status = QtWidgets.QLabel("")
        layout.addRow(self.lbl_update_status)
        
        self.tabs.addTab(behavior_tab, "Обновление")

    def _create_alerts_tab(self):
        """
        Вкладка “Оповещения”: настройки мигания и звукового сигнала
        """
        alerts_tab = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(alerts_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        settings = QtCore.QSettings("MyCompany", "TaskbarTimer")

        # Чекбокс «Включить мигание при окончании»
        self.chk_blink_enabled = QtWidgets.QCheckBox("Мигание при окончании")
        blink_enabled = settings.value("alerts/blink_enabled", False, type=bool)
        self.chk_blink_enabled.setChecked(blink_enabled)
        layout.addRow(self.chk_blink_enabled)

        # Поле «Частота мигания (Гц)»
        lbl_blink_freq = QtWidgets.QLabel("Частота мигания (Гц):")
        self.spin_blink_freq = QtWidgets.QSpinBox()
        self.spin_blink_freq.setRange(1, 10)
        raw_blink = settings.value("alerts/blink_freq", None)
        try:
            blink_freq = int(raw_blink) if raw_blink is not None else 2
        except (ValueError, TypeError):
            blink_freq = 2
        self.spin_blink_freq.setValue(blink_freq)
        layout.addRow(lbl_blink_freq, self.spin_blink_freq)

        # Чекбокс «Звуковой сигнал при окончании»
        self.chk_sound_enabled = QtWidgets.QCheckBox("Звуковой сигнал при окончании")
        sound_enabled = settings.value("alerts/sound_enabled", False, type=bool)
        self.chk_sound_enabled.setChecked(sound_enabled)
        layout.addRow(self.chk_sound_enabled)

        # Поле для пути к файлу звука
        lbl_sound = QtWidgets.QLabel("Звуковой файл:")
        self.edit_sound_path = QtWidgets.QLineEdit()
        saved_sound = settings.value("alerts/sound_file", "", type=str)
        self.edit_sound_path.setText(saved_sound)
        self.btn_browse = QtWidgets.QPushButton("Обзор...")
        self.btn_browse.clicked.connect(self._on_browse_sound)
        hl = QtWidgets.QHBoxLayout()
        hl.addWidget(self.edit_sound_path)
        hl.addWidget(self.btn_browse)
        layout.addRow(lbl_sound, hl)

        self.tabs.addTab(alerts_tab, "Оповещения")

    def _create_presets_tab(self):
        """
        Вкладка “Пресеты”: управление пресетами (таблица с сохранёнными значениями)
        """
        presets_tab = QtWidgets.QWidget()
        v_layout = QtWidgets.QVBoxLayout(presets_tab)
        v_layout.setContentsMargins(10, 10, 10, 10)
        v_layout.setSpacing(6)

        # Таблица пресетов
        self.table_presets = QtWidgets.QTableWidget(0, 2)
        self.table_presets.setHorizontalHeaderLabels(["Название", "Время (сек)"])
        self.table_presets.horizontalHeader().setStretchLastSection(True)
        v_layout.addWidget(self.table_presets)

        # Кнопки Добавить/Удалить пресет
        hl_buttons = QtWidgets.QHBoxLayout()
        self.btn_add_preset = QtWidgets.QPushButton("Добавить")
        self.btn_remove_preset = QtWidgets.QPushButton("Удалить")
        hl_buttons.addWidget(self.btn_add_preset)
        hl_buttons.addWidget(self.btn_remove_preset)
        hl_buttons.addStretch(1)
        v_layout.addLayout(hl_buttons)

        # Сигналы для работы с пресетами
        self.btn_add_preset.clicked.connect(self._on_add_preset)
        self.btn_remove_preset.clicked.connect(self._on_remove_preset)

        # Загрузка существующих пресетов
        self._load_presets()

        self.tabs.addTab(presets_tab, "Пресеты")

    def _on_theme_changed(self, idx: int) -> None:
        """
        Переключаем внутренний флаг темы (используется в TaskbarTimer).
        """
        self._theme = "dark" if idx == 0 else "light"

    def _on_pick_color(self):
        """
        Открыть диалог выбора цвета для прогресс-бара.
        """
        color = QtWidgets.QColorDialog.getColor(self._progress_color, self, "Выберите цвет прогресс-бара")
        if color.isValid():
            self._progress_color = color
            self._update_color_button(color)

    def _update_color_button(self, color: QtGui.QColor):
        """
        Обновить фон кнопки выбора цвета, чтобы показывать текущий выбор.
        """
        pixmap = QtGui.QPixmap(64, 24)
        pixmap.fill(color)
        icon = QtGui.QIcon(pixmap)
        self.btn_pick_color.setIcon(icon)
        self.btn_pick_color.setIconSize(pixmap.rect().size())

    def _on_browse_sound(self):
        """
        Открыть файловый диалог для выбора звукового файла.
        """
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Выберите звуковой файл", "", "WAV Files (*.wav)"
        )
        if path:
            self.edit_sound_path.setText(path)
            
    @log_exceptions
    def _load_presets(self):
        """
        Загрузить пресеты из QSettings (или другого хранилища).
        """
        self.table_presets.setRowCount(0)
        for item in load_raw_presets():
            row = self.table_presets.rowCount()
            self.table_presets.insertRow(row)
            self.table_presets.setItem(row, 0, QtWidgets.QTableWidgetItem(item["name"]))
            self.table_presets.setItem(row, 1, QtWidgets.QTableWidgetItem(str(item["minutes"])))

    @log_exceptions
    def _on_add_preset(self):
        """
        Добавить новый пресет: открываем диалог-подсказку, получаем имя и время.
        """
        name, ok1 = QtWidgets.QInputDialog.getText(self, "Новый пресет", "Название пресета:")
        if not ok1 or not name:
            return
        minutes, ok2 = QtWidgets.QInputDialog.getInt(self, "Новый пресет", "Время (в секундах):", min=1)
        if not ok2:
            return

        row = self.table_presets.rowCount()
        self.table_presets.insertRow(row)
        self.table_presets.setItem(row, 0, QtWidgets.QTableWidgetItem(name))
        self.table_presets.setItem(row, 1, QtWidgets.QTableWidgetItem(str(minutes)))

    @log_exceptions
    def _on_remove_preset(self):
        """
        Удалить выделенный пресет из таблицы.
        """
        selected = self.table_presets.currentRow()
        if selected >= 0:
            self.table_presets.removeRow(selected)

    def _on_apply_clicked(self):
        """
        Нажата кнопка Apply: сохраняем настройки, эмитим сигнал, но окно не закрываем.
        """
        self._save_and_emit()

    def _on_ok_clicked(self):
        """
        Нажата кнопка OK: сохраняем настройки, эмитим сигнал и закрываем окно.
        """
        self._save_and_emit()
        self.close()

    def _on_cancel_clicked(self):
        """
        Нажата кнопка Cancel: просто закрываем окно без сохранения.
        """
        self.close()

    @log_exceptions
    def _save_and_emit(self):
        """
        Сохранить все настройки из полей в QSettings и эмитить settings_changed().
        """
        settings = QtCore.QSettings("MyCompany", "TaskbarTimer")

        # 1) Общие
        settings.setValue("timer/always_on_top", self.chk_always_on_top.isChecked())
        settings.setValue("timer/minimize_to_tray", self.chk_minimize_to_tray.isChecked())
        settings.setValue("timer/auto_start", self.chk_auto_start.isChecked())

        # новая настройка: направление отсчёта
        count_dir = "up" if self.combo_count_dir.currentIndex() == 0 else "down"
        settings.setValue("timer/count_direction", count_dir)

        # 2) Тема и цвет прогресс-бара
        theme = "dark" if self.combo_theme.currentIndex() == 0 else "light"
        settings.setValue("appearance/theme", theme)
        settings.setValue("appearance/progress_color", self._progress_color.name())
        settings.setValue("appearance/font", getattr(self, "_font", "Arial"))
        settings.setValue("appearance/font_size", getattr(self, "_font_size", 12))
        
        # 3) Поведение (автообновление)
        settings.setValue("general/auto_update_enabled", self.chk_auto_update.isChecked())
        settings.setValue("general/update_interval", self.spin_update_interval.value())

        # 4) Оповещения (мигание и звук)
        settings.setValue("alerts/blink_enabled", self.chk_blink_enabled.isChecked())
        settings.setValue("alerts/blink_freq", self.spin_blink_freq.value())
        settings.setValue("alerts/sound_enabled", self.chk_sound_enabled.isChecked())
        settings.setValue("alerts/sound_file", self.edit_sound_path.text())

        # 5) Пресеты
        presets = []
        for row in range(self.table_presets.rowCount()):
            name_item = self.table_presets.item(row, 0)
            time_item = self.table_presets.item(row, 1)
            if name_item and time_item:
                name = name_item.text()
                try:
                    minutes = int(time_item.text())
                except ValueError:
                    minutes = 0
                presets.append((name, minutes))
        save_presets(presets)

        # Эмитируем сигнал, чтобы TaskbarTimer обновил настройки
        self.settings_changed.emit()
        
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Нажатие '×' или Alt+F4:
        • скрываем окно;
        • отменяем штатное закрытие (ignore),
          чтобы приложение не завершалось.
        """
        self.hide()
        event.ignore()
        
    @log_exceptions 
    def _on_check_updates(self, checked=False):
        """
        Запускается при клике «Проверить обновления…»
        Эмитит сигнал и меняет текст статуса.
        """
        self.lbl_update_status.setText("Идёт проверка…")
        self.check_updates.emit()