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
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QFont, QPainter, QPolygon

import config
from src.core.file_manager import FileManager


class RightPopupComboBox(QComboBox):
    """드롭다운이 오른쪽에 QMenu로 바로 나타나는 커스텀 콤보박스

    - 화살표: ▶ 오른쪽 방향 삼각형 직접 그리기
    - 팝업: QComboBox 기본 팝업 대신 QMenu 사용 → 깜빡임 없음
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px 30px 5px 10px;
                background-color: white;
            }
            QComboBox:hover {
                border: 1px solid #999;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 30px;
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
                width: 0;
                height: 0;
            }
        """)

    def paintEvent(self, event):
        """콤보박스를 그린 뒤, 플레이스홀더와 ▶ 화살표를 직접 그립니다."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 미선택 상태(currentIndex == -1)일 때 플레이스홀더 텍스트 직접 그리기
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
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 4px 0;
            }
            QMenu::item {
                padding: 6px 20px;
            }
            QMenu::item:selected {
                background-color: #e3f2fd;
            }
        """)

        for i in range(self.count()):
            action = menu.addAction(self.itemText(i))
            action.setData(i)

        # 콤보박스 오른쪽 끝 + 2px 간격에서 메뉴 표시
        pos = self.mapToGlobal(QPoint(self.width() + 2, 0))
        selected = menu.exec_(pos)
        if selected is not None:
            self.setCurrentIndex(selected.data())


class MainWindow(QMainWindow):
    """메인 애플리케이션 윈도우"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(config.APP_NAME)
        self.setGeometry(100, 100, config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        self.setMinimumSize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT)

        # FileManager 초기화
        self.file_manager = FileManager()

        # 현재 선택 상태 추적
        self.current_course = None
        self.current_textbook = None
        self.current_chapter = None

        # UI 구성
        self.init_ui()

        # 드롭다운 이벤트 연결
        self.connect_signals()

    def init_ui(self):
        """전체 UI를 구성합니다."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # 좌측 사이드바 (폴더 선택 + 드롭다운)
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar, 0)

        # 우측 메인 영역 (문제 목록)
        main_area = self.create_main_area()
        main_layout.addWidget(main_area, 1)

        # 하단 상태바
        self.create_status_bar()

    # ──────────────────────────────────────────────
    # 사이드바: 루트 디렉토리 선택 + 과정/교재/단원 드롭다운
    # ──────────────────────────────────────────────
    def create_sidebar(self):
        sidebar_frame = QFrame()
        sidebar_frame.setMinimumWidth(380)
        sidebar_frame.setMaximumWidth(380)
        sidebar_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f9f9f9;
            }
        """)

        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(15, 15, 15, 15)
        sidebar_layout.setSpacing(12)

        # ── 루트 디렉토리 선택 영역 ──
        root_label = QLabel("문제 DB 폴더")
        root_label.setFont(QFont(config.FONT_FAMILY, config.FONT_SIZE + 1, QFont.Bold))
        sidebar_layout.addWidget(root_label)

        # 현재 선택된 경로를 표시하는 라벨
        self.root_path_label = QLabel("선택되지 않음")
        self.root_path_label.setWordWrap(True)
        self.root_path_label.setStyleSheet("""
            QLabel {
                color: #666;
                padding: 5px;
                border: none;
                background-color: #f0f0f0;
                border-radius: 3px;
            }
        """)
        sidebar_layout.addWidget(self.root_path_label)

        # 폴더 선택 버튼
        self.select_root_btn = QPushButton("폴더 선택")
        self.select_root_btn.setMinimumHeight(35)
        self.select_root_btn.setCursor(Qt.PointingHandCursor)
        sidebar_layout.addWidget(self.select_root_btn)

        # 구분선
        self._add_separator(sidebar_layout)

        # ── 과정 선택 드롭다운 ──
        self.course_combo = RightPopupComboBox()
        self.course_combo.setPlaceholderText("과정을 선택하세요")
        self.course_combo.setCurrentIndex(-1)
        self.course_combo.setMinimumHeight(35)
        self.course_combo.setEnabled(False)
        sidebar_layout.addWidget(self.course_combo)

        # ── 교재 선택 드롭다운 ──
        self.textbook_combo = RightPopupComboBox()
        self.textbook_combo.setPlaceholderText("교재를 선택하세요")
        self.textbook_combo.setCurrentIndex(-1)
        self.textbook_combo.setMinimumHeight(35)
        self.textbook_combo.setEnabled(False)
        sidebar_layout.addWidget(self.textbook_combo)

        # ── 단원 선택 드롭다운 ──
        self.chapter_combo = RightPopupComboBox()
        self.chapter_combo.setPlaceholderText("단원을 선택하세요")
        self.chapter_combo.setCurrentIndex(-1)
        self.chapter_combo.setMinimumHeight(35)
        self.chapter_combo.setEnabled(False)
        sidebar_layout.addWidget(self.chapter_combo)

        # 구분선
        self._add_separator(sidebar_layout)

        # 설정 버튼
        settings_btn = QPushButton("설정")
        settings_btn.setMinimumHeight(40)
        settings_btn.setCursor(Qt.PointingHandCursor)
        sidebar_layout.addWidget(settings_btn)

        # 남은 공간 채우기
        sidebar_layout.addStretch()

        return sidebar_frame

    # ──────────────────────────────────────────────
    # 메인 영역: 문제 목록 + 액션 버튼
    # ──────────────────────────────────────────────
    def create_main_area(self):
        main_frame = QFrame()
        main_layout = QVBoxLayout(main_frame)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # 헤더: 제목 + 선택 개수
        header_layout = QHBoxLayout()
        self.chapter_title = QLabel("문제 선택")
        self.chapter_title.setFont(QFont(config.FONT_FAMILY, config.FONT_SIZE + 2, QFont.Bold))
        header_layout.addWidget(self.chapter_title)
        header_layout.addStretch()
        self.selection_label = QLabel("선택됨: 0/0")
        header_layout.addWidget(self.selection_label)
        main_layout.addLayout(header_layout)

        # 툴바: 전체선택/해제 버튼
        toolbar_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("전체선택")
        self.select_all_btn.setMaximumWidth(100)
        self.select_all_btn.setCursor(Qt.PointingHandCursor)
        toolbar_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("전체해제")
        self.deselect_all_btn.setMaximumWidth(100)
        self.deselect_all_btn.setCursor(Qt.PointingHandCursor)
        toolbar_layout.addWidget(self.deselect_all_btn)
        toolbar_layout.addStretch()
        main_layout.addLayout(toolbar_layout)

        # 문제 목록 (체크박스 포함)
        self.problem_list = QListWidget()
        self.problem_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #ffffff;
            }
            QListWidget::item {
                padding: 8px;
            }
        """)
        main_layout.addWidget(self.problem_list)

        # 액션 버튼들
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        for text in ["미리보기", "출력", "저장"]:
            btn = QPushButton(text)
            btn.setMinimumHeight(40)
            btn.setCursor(Qt.PointingHandCursor)
            button_layout.addWidget(btn)
        main_layout.addLayout(button_layout)

        return main_frame

    def create_status_bar(self):
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.showMessage("준비 완료 - 루트 디렉토리를 선택해주세요")

    # ──────────────────────────────────────────────
    # 시그널 연결: 버튼 클릭, 드롭다운 변경 이벤트
    # ──────────────────────────────────────────────
    def connect_signals(self):
        """모든 UI 이벤트를 핸들러에 연결합니다."""
        # 루트 폴더 선택 버튼
        self.select_root_btn.clicked.connect(self.on_select_root)

        # 드롭다운 변경 시 → 하위 드롭다운 업데이트
        # currentIndexChanged(int)를 사용: 인덱스 0은 플레이스홀더
        self.course_combo.currentIndexChanged.connect(self.on_course_changed)
        self.textbook_combo.currentIndexChanged.connect(self.on_textbook_changed)
        self.chapter_combo.currentIndexChanged.connect(self.on_chapter_changed)

        # 전체선택/해제 버튼
        self.select_all_btn.clicked.connect(self.on_select_all)
        self.deselect_all_btn.clicked.connect(self.on_deselect_all)

    # ──────────────────────────────────────────────
    # 이벤트 핸들러들
    # ──────────────────────────────────────────────
    def on_select_root(self):
        """루트 디렉토리를 선택하는 폴더 브라우저를 엽니다."""
        folder = QFileDialog.getExistingDirectory(
            self, "루트 디렉토리 선택", "",
            QFileDialog.ShowDirsOnly
        )
        if not folder:
            return  # 사용자가 취소한 경우

        # FileManager에 루트 설정
        self.file_manager.set_root(folder)
        self.root_path_label.setText(folder)

        # 과정 드롭다운 채우기
        courses = self.file_manager.get_courses()
        self.course_combo.blockSignals(True)
        self.course_combo.clear()
        self.course_combo.addItems(courses)
        self.course_combo.setCurrentIndex(-1)  # 플레이스홀더 표시
        self.course_combo.blockSignals(False)
        self.course_combo.setEnabled(len(courses) > 0)

        # 하위 드롭다운 초기화
        self._reset_textbook_combo()
        self._reset_chapter_combo()
        self._clear_problem_list()

        self.statusBar().showMessage(f"루트 디렉토리 설정 완료: {folder} ({len(courses)}개 과정)")

    def on_course_changed(self, index):
        """과정이 변경되면 → 교재 드롭다운을 업데이트합니다."""
        # 하위 항목들 초기화
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

        self.statusBar().showMessage(
            f"과정: {self.current_course} ({len(textbooks)}개 교재)"
        )

    def on_textbook_changed(self, index):
        """교재가 변경되면 → 단원 드롭다운을 업데이트합니다."""
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

        self.statusBar().showMessage(
            f"교재: {self.current_textbook} ({len(chapters)}개 단원)"
        )

    def on_chapter_changed(self, index):
        """단원이 변경되면 → 문제 이미지 목록을 표시합니다."""
        self._clear_problem_list()

        if index < 0 or not self.current_course or not self.current_textbook:
            self.current_chapter = None

            return

        self.current_chapter = self.chapter_combo.currentText()

        problems = self.file_manager.get_problems(
            self.current_course, self.current_textbook, self.current_chapter
        )

        # 헤더 타이틀 업데이트
        self.chapter_title.setText(f"문제 선택 (단원: {self.current_chapter})")

        # 문제 목록에 체크박스 아이템 추가
        for problem_name in problems:
            item = QListWidgetItem()
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setText(problem_name)
            self.problem_list.addItem(item)

        self._update_selection_count()
        self.statusBar().showMessage(
            f"단원: {self.current_chapter} ({len(problems)}개 문제)"
        )

    # ──────────────────────────────────────────────
    # 전체선택 / 전체해제
    # ──────────────────────────────────────────────
    def on_select_all(self):
        """모든 문제를 선택합니다."""
        for i in range(self.problem_list.count()):
            self.problem_list.item(i).setCheckState(Qt.Checked)
        self._update_selection_count()

    def on_deselect_all(self):
        """모든 문제 선택을 해제합니다."""
        for i in range(self.problem_list.count()):
            self.problem_list.item(i).setCheckState(Qt.Unchecked)
        self._update_selection_count()

    # ──────────────────────────────────────────────
    # 헬퍼 메서드들
    # ──────────────────────────────────────────────
    def _reset_textbook_combo(self):
        """교재 드롭다운을 초기 상태로 리셋합니다."""
        self.textbook_combo.blockSignals(True)
        self.textbook_combo.clear()
        self.textbook_combo.setCurrentIndex(-1)
        self.textbook_combo.setEnabled(False)
        self.textbook_combo.blockSignals(False)
        self.current_textbook = None

    def _reset_chapter_combo(self):
        """단원 드롭다운을 초기 상태로 리셋합니다."""
        self.chapter_combo.blockSignals(True)
        self.chapter_combo.clear()
        self.chapter_combo.setCurrentIndex(-1)
        self.chapter_combo.setEnabled(False)
        self.chapter_combo.blockSignals(False)
        self.current_chapter = None

    def _clear_problem_list(self):
        """문제 목록을 비웁니다."""
        self.problem_list.clear()
        self.chapter_title.setText("문제 선택")
        self._update_selection_count()

    def _update_selection_count(self):
        """선택된 문제 개수를 업데이트합니다."""
        total = self.problem_list.count()
        checked = sum(
            1 for i in range(total)
            if self.problem_list.item(i).checkState() == Qt.Checked
        )
        self.selection_label.setText(f"선택됨: {checked}/{total}")

    def _add_separator(self, layout):
        """구분선을 추가합니다."""
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("border: none; border-top: 1px solid #ccc;")
        layout.addWidget(separator)
