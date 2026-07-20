"""
메인 윈도우 - 수학 오답노트 프로그램의 메인 화면
"""
import sys
import ctypes
import ctypes.wintypes
from pathlib import Path
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QPushButton, QListWidget, QListWidgetItem,
    QCheckBox, QStatusBar, QFrame, QFileDialog, QMessageBox, QMenu,
    QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, QPoint, QRect, QSize
from PyQt5.QtGui import QFont, QPainter, QPolygon, QColor, QCursor

import config
from src.core.file_manager import FileManager
from src.ui import widget_style as S


class RightPopupComboBox(QComboBox):
    """드롭다운이 오른쪽에 QMenu로 바로 나타나는 커스텀 콤보박스"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(S.COMBOBOX)

    def paintEvent(self, event):
        """콤보박스를 그린 뒤, 플레이스홀더와 ▶ 화살표를 직접 그립니다."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 미선택 상태일 때 플레이스홀더 텍스트 직접 그리기
        if self.currentIndex() < 0 and self.placeholderText():
            painter.setPen(Qt.gray)
            text_rect = self.rect().adjusted(12, 0, -35, 0)
            painter.drawText(text_rect, Qt.AlignVCenter, self.placeholderText())

        # ▶ 오른쪽 화살표
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.darkGray)
        x = self.width() - 18
        y = self.height() // 2
        size = 5
        triangle = QPolygon([
            QPoint(x - size, y - size),
            QPoint(x + size, y),
            QPoint(x - size, y + size),
        ])
        painter.drawPolygon(triangle)
        painter.end()

    def showPopup(self):
        """기본 팝업 대신 QMenu를 콤보박스 오른쪽에 바로 표시합니다."""
        if self.count() == 0:
            return

        menu = QMenu(self)
        menu.setWindowFlags(menu.windowFlags() | Qt.NoDropShadowWindowHint)
        menu.setStyleSheet(S.COMBOBOX_MENU)

        for i in range(self.count()):
            action = menu.addAction(self.itemText(i))
            action.setData(i)

        menu.setMinimumWidth(450)  # 콤보박스와 같은 너비 이상 확보
        pos = self.mapToGlobal(QPoint(self.width() + 10, 0))
        selected = menu.exec_(pos)
        if selected is not None:
            self.setCurrentIndex(selected.data())


class MainWindow(QMainWindow):
    """메인 애플리케이션 윈도우"""

    RESIZE_MARGIN = 8

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMouseTracking(True)

        self.setGeometry(100, 100, config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        self.setMinimumSize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT)

        self._drag_pos = None

        self.file_manager = FileManager()

        self.current_course = None
        self.current_textbook = None
        self.current_chapter = None

        self._is_maximized = False

        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        self.setStyleSheet(S.MAIN_WINDOW)

        central_widget = QWidget()
        central_widget.setMouseTracking(True)
        self.setCentralWidget(central_widget)

        outer_layout = QVBoxLayout(central_widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        header = self.create_header()
        outer_layout.addWidget(header)

        body_widget = QWidget()
        body_widget.setStyleSheet(f"background-color: {S.BG_BODY};")
        body_layout = QHBoxLayout(body_widget)
        body_layout.setContentsMargins(16, 16, 16, 16)
        body_layout.setSpacing(16)

        sidebar = self.create_sidebar()
        body_layout.addWidget(sidebar, 0)

        main_area = self.create_main_area()
        body_layout.addWidget(main_area, 1)

        outer_layout.addWidget(body_widget, 1)

        self.create_status_bar()

    # ──────────────────────────────────────────────
    # 커스텀 타이틀바
    # ──────────────────────────────────────────────
    def create_header(self):
        self._header = QFrame()
        self._header.setFixedHeight(80)
        self._header.setStyleSheet(S.HEADER)

        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(16, 0, 8, 0)
        header_layout.setSpacing(6)

        title = QLabel(config.APP_NAME)
        title.setStyleSheet(S.HEADER_TITLE)
        header_layout.addWidget(title)

        header_layout.addStretch()

        version = QLabel(f"v{config.APP_VERSION}")
        version.setStyleSheet(S.HEADER_VERSION)
        header_layout.addWidget(version)

        # 창 컨트롤 버튼
        ctrl_style = S.WINDOW_CTRL_BTN

        self.btn_minimize = QPushButton("─")
        self.btn_minimize.setFixedSize(36, 32)
        self.btn_minimize.setCursor(Qt.PointingHandCursor)
        self.btn_minimize.setStyleSheet(ctrl_style.format(size=25, hover=S.CTRL_BTN_HOVER))
        self.btn_minimize.clicked.connect(self.showMinimized)
        header_layout.addWidget(self.btn_minimize)

        self.btn_maximize = QPushButton("□")
        self.btn_maximize.setFixedSize(36, 32)
        self.btn_maximize.setCursor(Qt.PointingHandCursor)
        self.btn_maximize.setStyleSheet(ctrl_style.format(size=25, hover=S.CTRL_BTN_HOVER))
        self.btn_maximize.clicked.connect(self.toggle_maximize)
        header_layout.addWidget(self.btn_maximize)

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(36, 32)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setStyleSheet(ctrl_style.format(size=25, hover=S.RED_CLOSE))
        self.btn_close.clicked.connect(self.close)
        header_layout.addWidget(self.btn_close)

        return self._header

    def toggle_maximize(self):
        if self._is_maximized:
            self.showNormal()
        else:
            self.showMaximized()

    # ──────────────────────────────────────────────
    # 사이드바
    # ──────────────────────────────────────────────
    def create_sidebar(self):
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("sidebar")
        sidebar_frame.setMinimumWidth(400)
        sidebar_frame.setMaximumWidth(400)
        sidebar_frame.setStyleSheet(S.SIDEBAR)

        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(18, 18, 18, 18)
        sidebar_layout.setSpacing(14)

        root_label = QLabel("Root Dir")
        root_label.setStyleSheet(S.SECTION_LABEL)
        sidebar_layout.addWidget(root_label)

        self.root_path_label = QLabel("선택되지 않음")
        self.root_path_label.setWordWrap(True)
        self.root_path_label.setStyleSheet(S.PATH_LABEL)
        sidebar_layout.addWidget(self.root_path_label)

        self.select_root_btn = QPushButton("폴더 선택")
        self.select_root_btn.setMinimumHeight(45)
        self.select_root_btn.setCursor(Qt.PointingHandCursor)
        self.select_root_btn.setStyleSheet(S.BTN_PRIMARY)
        sidebar_layout.addWidget(self.select_root_btn)

        self._add_separator(sidebar_layout)

        self.course_combo = RightPopupComboBox()
        self.course_combo.setPlaceholderText("과정을 선택하세요")
        self.course_combo.setCurrentIndex(-1)
        self.course_combo.setMinimumHeight(40)
        self.course_combo.setEnabled(False)
        sidebar_layout.addWidget(self.course_combo)

        self.textbook_combo = RightPopupComboBox()
        self.textbook_combo.setPlaceholderText("교재를 선택하세요")
        self.textbook_combo.setCurrentIndex(-1)
        self.textbook_combo.setMinimumHeight(40)
        self.textbook_combo.setEnabled(False)
        sidebar_layout.addWidget(self.textbook_combo)

        self.chapter_combo = RightPopupComboBox()
        self.chapter_combo.setPlaceholderText("단원을 선택하세요")
        self.chapter_combo.setCurrentIndex(-1)
        self.chapter_combo.setMinimumHeight(40)
        self.chapter_combo.setEnabled(False)
        sidebar_layout.addWidget(self.chapter_combo)

        self._add_separator(sidebar_layout)

        settings_btn = QPushButton("설정")
        settings_btn.setMinimumHeight(38)
        settings_btn.setCursor(Qt.PointingHandCursor)
        settings_btn.setStyleSheet(S.BTN_SECONDARY)
        sidebar_layout.addWidget(settings_btn)

        sidebar_layout.addStretch()

        return sidebar_frame

    # ──────────────────────────────────────────────
    # 메인 영역
    # ──────────────────────────────────────────────
    def create_main_area(self):
        main_frame = QFrame()
        main_frame.setObjectName("mainArea")
        main_frame.setStyleSheet(S.MAIN_AREA)

        main_layout = QVBoxLayout(main_frame)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(12)

        # 헤더
        header_layout = QHBoxLayout()
        self.chapter_title = QLabel("문제 선택")
        self.chapter_title.setMinimumHeight(40)
        self.chapter_title.setStyleSheet(S.MAIN_TITLE)
        header_layout.addWidget(self.chapter_title)
        header_layout.addStretch()

        self.selection_label = QLabel("선택됨: 0/0")
        self.selection_label.setStyleSheet(S.SELECTION_BADGE)
        header_layout.addWidget(self.selection_label)
        main_layout.addLayout(header_layout)

        # 툴바
        toolbar_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("전체선택")
        self.select_all_btn.setMaximumWidth(130)
        self.select_all_btn.setCursor(Qt.PointingHandCursor)
        self.select_all_btn.setStyleSheet(S.BTN_TOOLBAR)
        toolbar_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("전체해제")
        self.deselect_all_btn.setMaximumWidth(130)
        self.deselect_all_btn.setCursor(Qt.PointingHandCursor)
        self.deselect_all_btn.setStyleSheet(S.BTN_TOOLBAR)
        toolbar_layout.addWidget(self.deselect_all_btn)
        toolbar_layout.addStretch()
        main_layout.addLayout(toolbar_layout)

        # 문제 목록 (5열 그리드)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(S.PROBLEM_LIST)

        self.problem_grid_widget = QWidget()
        self.problem_grid = QGridLayout(self.problem_grid_widget)
        self.problem_grid.setSpacing(6)
        self.problem_grid.setContentsMargins(8, 8, 8, 8)
        scroll_area.setWidget(self.problem_grid_widget)
        main_layout.addWidget(scroll_area)

        self.problem_checkboxes = []

        # 출력 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.print_btn = QPushButton("노트 생성")
        self.print_btn.setMinimumHeight(50)
        self.print_btn.setCursor(Qt.PointingHandCursor)
        self.print_btn.setStyleSheet(S.BTN_PRINT)
        self.print_btn.setMinimumWidth(300)
        button_layout.addWidget(self.print_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        return main_frame

    def create_status_bar(self):
        status_bar = QStatusBar()
        status_bar.setStyleSheet(S.STATUS_BAR)
        self.setStatusBar(status_bar)
        status_bar.showMessage("준비 완료 - 루트 디렉토리를 선택해주세요")

    # ──────────────────────────────────────────────
    # 시그널 연결
    # ──────────────────────────────────────────────
    def connect_signals(self):
        self.select_root_btn.clicked.connect(self.on_select_root)
        self.course_combo.currentIndexChanged.connect(self.on_course_changed)
        self.textbook_combo.currentIndexChanged.connect(self.on_textbook_changed)
        self.chapter_combo.currentIndexChanged.connect(self.on_chapter_changed)
        self.select_all_btn.clicked.connect(self.on_select_all)
        self.deselect_all_btn.clicked.connect(self.on_deselect_all)
        self.print_btn.clicked.connect(self.on_create_note)

    # ──────────────────────────────────────────────
    # 이벤트 핸들러
    # ──────────────────────────────────────────────
    def on_select_root(self):
        folder = QFileDialog.getExistingDirectory(
            self, "루트 디렉토리 선택", "", QFileDialog.ShowDirsOnly
        )
        if not folder:
            return

        self.file_manager.set_root(folder)
        self.root_path_label.setText(folder)

        courses = self.file_manager.get_courses()
        self.course_combo.blockSignals(True)
        self.course_combo.clear()
        self.course_combo.addItems(courses)
        self.course_combo.setCurrentIndex(-1)
        self.course_combo.blockSignals(False)
        self.course_combo.setEnabled(len(courses) > 0)

        self._reset_textbook_combo()
        self._reset_chapter_combo()
        self._clear_problem_list()

        self.statusBar().showMessage(f"루트 디렉토리 설정 완료: {folder} ({len(courses)}개 과정)")

    def on_course_changed(self, index):
        self._reset_textbook_combo()
        self._reset_chapter_combo()
        self._clear_problem_list()

        if index < 0:
            self.current_course = None
            return

        self.current_course = self.course_combo.currentText()
        textbooks = self.file_manager.get_textbooks(self.current_course)

        self.textbook_combo.blockSignals(True)
        self.textbook_combo.clear()
        self.textbook_combo.addItems(textbooks)
        self.textbook_combo.setCurrentIndex(-1)
        self.textbook_combo.blockSignals(False)
        self.textbook_combo.setEnabled(len(textbooks) > 0)

        self.statusBar().showMessage(f"과정: {self.current_course} ({len(textbooks)}개 교재)")

    def on_textbook_changed(self, index):
        self._reset_chapter_combo()
        self._clear_problem_list()

        if index < 0 or not self.current_course:
            self.current_textbook = None
            return

        self.current_textbook = self.textbook_combo.currentText()
        chapters = self.file_manager.get_chapters(self.current_course, self.current_textbook)

        self.chapter_combo.blockSignals(True)
        self.chapter_combo.clear()
        self.chapter_combo.addItems(chapters)
        self.chapter_combo.setCurrentIndex(-1)
        self.chapter_combo.blockSignals(False)
        self.chapter_combo.setEnabled(len(chapters) > 0)

        self.statusBar().showMessage(f"교재: {self.current_textbook} ({len(chapters)}개 단원)")

    def on_chapter_changed(self, index):
        self._clear_problem_list()

        if index < 0 or not self.current_course or not self.current_textbook:
            self.current_chapter = None
            return

        self.current_chapter = self.chapter_combo.currentText()
        problems = self.file_manager.get_problems(
            self.current_course, self.current_textbook, self.current_chapter
        )

        cols = 5
        for i, problem_name in enumerate(problems):
            cb = QCheckBox(Path(problem_name).stem)
            cb.setProperty("filename", problem_name)
            cb.setStyleSheet(S.PROBLEM_ITEM)
            cb.setCursor(Qt.PointingHandCursor)
            cb.stateChanged.connect(lambda: self._update_selection_count())
            self.problem_checkboxes.append(cb)
            self.problem_grid.addWidget(cb, i // cols, i % cols)

        # 남은 공간을 아래로 밀어서 위쪽 정렬
        next_row = (len(problems) + cols - 1) // cols
        self.problem_grid.setRowStretch(next_row, 1)

        self._update_selection_count()
        self.statusBar().showMessage(f"단원: {self.current_chapter} ({len(problems)}개 문제)")

    # ──────────────────────────────────────────────
    # 전체선택 / 전체해제
    # ──────────────────────────────────────────────
    def on_select_all(self):
        for cb in self.problem_checkboxes:
            cb.setChecked(True)

    def on_deselect_all(self):
        for cb in self.problem_checkboxes:
            cb.setChecked(False)

    def on_create_note(self):
        checked = [cb for cb in self.problem_checkboxes if cb.isChecked()]
        if not checked:
            self.statusBar().showMessage("문제를 선택해주세요")
            return

        image_paths = []
        for cb in checked:
            filename = cb.property("filename")
            path = self.file_manager.get_problem_path(
                self.current_course, self.current_textbook,
                self.current_chapter, filename
            )
            image_paths.append(path)

        header_info = {
            "course": self.current_course,
            "textbook": self.current_textbook,
            "chapter": self.current_chapter,
            "format": "horizontal",
            "include_answer_sheet": True,
        }

        from src.utils.create_note import NotePreviewDialog
        dialog = NotePreviewDialog(image_paths, header_info, self)
        dialog.exec_()

    # ──────────────────────────────────────────────
    # 헬퍼 메서드
    # ──────────────────────────────────────────────
    def _reset_textbook_combo(self):
        self.textbook_combo.blockSignals(True)
        self.textbook_combo.clear()
        self.textbook_combo.setCurrentIndex(-1)
        self.textbook_combo.setEnabled(False)
        self.textbook_combo.blockSignals(False)
        self.current_textbook = None

    def _reset_chapter_combo(self):
        self.chapter_combo.blockSignals(True)
        self.chapter_combo.clear()
        self.chapter_combo.setCurrentIndex(-1)
        self.chapter_combo.setEnabled(False)
        self.chapter_combo.blockSignals(False)
        self.current_chapter = None

    def _clear_problem_list(self):
        for cb in self.problem_checkboxes:
            cb.deleteLater()
        self.problem_checkboxes.clear()
        # stretch 리셋
        for i in range(self.problem_grid.rowCount()):
            self.problem_grid.setRowStretch(i, 0)
        self._update_selection_count()

    def _update_selection_count(self):
        total = len(self.problem_checkboxes)
        checked = sum(1 for cb in self.problem_checkboxes if cb.isChecked())
        self.selection_label.setText(f"선택됨: {checked}/{total}")

    def _add_separator(self, layout):
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet(S.SEPARATOR)
        layout.addWidget(separator)

    # ──────────────────────────────────────────────
    # 타이틀바 드래그 이동 + 더블클릭 최대화 + 창 리사이즈
    # ──────────────────────────────────────────────
    def _is_on_header(self, pos):
        return self._header.geometry().contains(pos)

    def nativeEvent(self, eventType, message):
        """Windows WM_NCHITTEST를 처리하여 창 리사이즈 및 드래그 이동을 지원합니다."""
        if eventType == b"windows_generic_MSG":
            msg = ctypes.wintypes.MSG.from_address(int(message))
            if msg.message == 0x0084:  # WM_NCHITTEST
                pos = self.mapFromGlobal(QPoint(
                    ctypes.c_short(msg.lParam & 0xFFFF).value,
                    ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value,
                ))
                x, y = pos.x(), pos.y()
                w, h = self.width(), self.height()
                m = self.RESIZE_MARGIN

                if not self._is_maximized:
                    # 코너
                    if x < m and y < m:
                        return True, 13  # HTTOPLEFT
                    if x > w - m and y < m:
                        return True, 14  # HTTOPRIGHT
                    if x < m and y > h - m:
                        return True, 16  # HTBOTTOMLEFT
                    if x > w - m and y > h - m:
                        return True, 17  # HTBOTTOMRIGHT
                    # 엣지
                    if x < m:
                        return True, 10  # HTLEFT
                    if x > w - m:
                        return True, 11  # HTRIGHT
                    if y < m:
                        return True, 12  # HTTOP
                    if y > h - m:
                        return True, 15  # HTBOTTOM

                # 헤더 영역 → 타이틀바 드래그 (버튼 영역 제외)
                if self._is_on_header(pos):
                    for btn in (self.btn_minimize, self.btn_maximize, self.btn_close):
                        btn_rect = btn.geometry()
                        btn_pos = btn.parentWidget().mapTo(self, btn_rect.topLeft())
                        mapped = QRect(btn_pos, btn_rect.size())
                        if mapped.contains(pos):
                            return False, 0  # Qt가 버튼 클릭을 처리
                    return True, 2  # HTCAPTION

        return super().nativeEvent(eventType, message)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

    def changeEvent(self, event):
        """OS 최대화/복원 이벤트와 커스텀 상태를 동기화합니다."""
        from PyQt5.QtCore import QEvent
        if event.type() == QEvent.WindowStateChange:
            if self.windowState() & Qt.WindowMaximized:
                self._is_maximized = True
                self.btn_maximize.setText("❐")
            elif not (self.windowState() & Qt.WindowMinimized):
                self._is_maximized = False
                self.btn_maximize.setText("□")
        super().changeEvent(event)
