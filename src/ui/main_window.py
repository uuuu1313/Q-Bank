"""
메인 윈도우 - 수학 오답노트 프로그램의 메인 화면
"""
import sys
from pathlib import Path
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QListWidget, QListWidgetItem,
    QCheckBox, QStatusBar, QFrame, QFileDialog, QMessageBox, QMenu
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
        menu.setStyleSheet(S.COMBOBOX_MENU)

        for i in range(self.count()):
            action = menu.addAction(self.itemText(i))
            action.setData(i)

        pos = self.mapToGlobal(QPoint(self.width() + 2, 0))
        selected = menu.exec_(pos)
        if selected is not None:
            self.setCurrentIndex(selected.data())


class MainWindow(QMainWindow):
    """메인 애플리케이션 윈도우"""

    RESIZE_MARGIN = 6

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.setGeometry(100, 100, config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        self.setMinimumSize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT)

        self._drag_pos = None
        self._resizing = False
        self._resize_dir = None

        self.file_manager = FileManager()

        self.current_course = None
        self.current_textbook = None
        self.current_chapter = None

        self._is_maximized = False
        self._normal_geometry = None

        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        self.setStyleSheet(S.MAIN_WINDOW)

        central_widget = QWidget()
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
        title.setFont(QFont(config.FONT_FAMILY, S.FONT_SIZE_TITLE_BAR, QFont.Bold))
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
            if self._normal_geometry:
                self.setGeometry(self._normal_geometry)
            self._is_maximized = False
            self.btn_maximize.setText("□")
        else:
            self._normal_geometry = self.geometry()
            from PyQt5.QtWidgets import QDesktopWidget
            screen = QDesktopWidget().availableGeometry(self)
            self.setGeometry(screen)
            self._is_maximized = True
            self.btn_maximize.setText("❐")

    # ──────────────────────────────────────────────
    # 사이드바
    # ──────────────────────────────────────────────
    def create_sidebar(self):
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("sidebar")
        sidebar_frame.setMinimumWidth(300)
        sidebar_frame.setMaximumWidth(300)
        sidebar_frame.setStyleSheet(S.SIDEBAR)

        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(18, 18, 18, 18)
        sidebar_layout.setSpacing(14)

        root_label = QLabel("문제 DB 폴더")
        root_label.setFont(QFont(config.FONT_FAMILY, S.FONT_SIZE_SECTION_TITLE, QFont.Bold))
        root_label.setStyleSheet(S.SECTION_LABEL)
        sidebar_layout.addWidget(root_label)

        self.root_path_label = QLabel("선택되지 않음")
        self.root_path_label.setWordWrap(True)
        self.root_path_label.setStyleSheet(S.PATH_LABEL)
        sidebar_layout.addWidget(self.root_path_label)

        self.select_root_btn = QPushButton("폴더 선택")
        self.select_root_btn.setMinimumHeight(38)
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
        self.chapter_title.setFont(QFont(config.FONT_FAMILY, S.FONT_SIZE_MAIN_TITLE, QFont.Bold))
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

        # 문제 목록
        self.problem_list = QListWidget()
        self.problem_list.setStyleSheet(S.PROBLEM_LIST)
        main_layout.addWidget(self.problem_list)

        # 액션 버튼
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        action_buttons = [
            ("미리보기", S.BTN_PREVIEW),
            ("출력", S.BTN_PRINT),
            ("저장", S.BTN_SAVE),
        ]
        for text, style in action_buttons:
            btn = QPushButton(text)
            btn.setMinimumHeight(42)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(style)
            button_layout.addWidget(btn)
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

        self.chapter_title.setText(f"문제 선택 (단원: {self.current_chapter})")

        for problem_name in problems:
            item = QListWidgetItem()
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setText(problem_name)
            self.problem_list.addItem(item)

        self._update_selection_count()
        self.statusBar().showMessage(f"단원: {self.current_chapter} ({len(problems)}개 문제)")

    # ──────────────────────────────────────────────
    # 전체선택 / 전체해제
    # ──────────────────────────────────────────────
    def on_select_all(self):
        for i in range(self.problem_list.count()):
            self.problem_list.item(i).setCheckState(Qt.Checked)
        self._update_selection_count()

    def on_deselect_all(self):
        for i in range(self.problem_list.count()):
            self.problem_list.item(i).setCheckState(Qt.Unchecked)
        self._update_selection_count()

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
        self.problem_list.clear()
        self.chapter_title.setText("문제 선택")
        self._update_selection_count()

    def _update_selection_count(self):
        total = self.problem_list.count()
        checked = sum(
            1 for i in range(total)
            if self.problem_list.item(i).checkState() == Qt.Checked
        )
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

    def _get_resize_direction(self, pos):
        m = self.RESIZE_MARGIN
        rect = self.rect()
        x, y = pos.x(), pos.y()

        left = x < m
        right = x > rect.width() - m
        top = y < m
        bottom = y > rect.height() - m

        if top and left:     return "top-left"
        if top and right:    return "top-right"
        if bottom and left:  return "bottom-left"
        if bottom and right: return "bottom-right"
        if left:             return "left"
        if right:            return "right"
        if top:              return "top"
        if bottom:           return "bottom"
        return None

    def _get_resize_cursor(self, direction):
        cursors = {
            "left": Qt.SizeHorCursor,
            "right": Qt.SizeHorCursor,
            "top": Qt.SizeVerCursor,
            "bottom": Qt.SizeVerCursor,
            "top-left": Qt.SizeFDiagCursor,
            "bottom-right": Qt.SizeFDiagCursor,
            "top-right": Qt.SizeBDiagCursor,
            "bottom-left": Qt.SizeBDiagCursor,
        }
        return cursors.get(direction, Qt.ArrowCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            direction = self._get_resize_direction(event.pos())
            if direction and not self._is_maximized:
                self._resizing = True
                self._resize_dir = direction
                self._drag_pos = event.globalPos()
                self._start_geometry = self.geometry()
                return

            if self._is_on_header(event.pos()):
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resizing and self._resize_dir:
            diff = event.globalPos() - self._drag_pos
            geo = QRect(self._start_geometry)
            min_w, min_h = self.minimumWidth(), self.minimumHeight()

            d = self._resize_dir
            if "right" in d:
                geo.setWidth(max(min_w, self._start_geometry.width() + diff.x()))
            if "bottom" in d:
                geo.setHeight(max(min_h, self._start_geometry.height() + diff.y()))
            if "left" in d:
                new_w = self._start_geometry.width() - diff.x()
                if new_w >= min_w:
                    geo.setLeft(self._start_geometry.left() + diff.x())
            if "top" in d:
                new_h = self._start_geometry.height() - diff.y()
                if new_h >= min_h:
                    geo.setTop(self._start_geometry.top() + diff.y())

            self.setGeometry(geo)
            return

        if self._drag_pos and not self._resizing:
            if self._is_maximized:
                self._is_maximized = False
                self.btn_maximize.setText("□")
                if self._normal_geometry:
                    ratio = event.globalPos().x() / self.width()
                    self.setGeometry(self._normal_geometry)
                    new_x = event.globalPos().x() - int(self.width() * ratio)
                    self.move(new_x, event.globalPos().y() - 24)
                    self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            else:
                self.move(event.globalPos() - self._drag_pos)
            return

        if not self._is_maximized:
            direction = self._get_resize_direction(event.pos())
            if direction:
                self.setCursor(self._get_resize_cursor(direction))
            else:
                self.unsetCursor()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self._resizing = False
        self._resize_dir = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and self._is_on_header(event.pos()):
            self.toggle_maximize()
        super().mouseDoubleClickEvent(event)
