"""
오답노트 페이지 생성 및 미리보기 다이얼로그.

create_note_pages: 이미지 경로 리스트를 받아 A4 페이지로 렌더링한 QPixmap 리스트 반환.
NotePreviewDialog: 미리보기 + 출력 + PDF 저장 UI.
"""

from pathlib import Path

from PIL import Image
from PyQt5.QtCore import Qt, QSize, QTimer, QRect
from PyQt5.QtGui import QPainter, QImage, QPixmap, QColor, QFont, QPen, QBrush
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel, QPushButton,
    QSpinBox, QFileDialog, QMessageBox, QFrame, QWidget, QLineEdit,
)

import config
from src.ui import widget_style as S
from src.utils.pdf_export import save_pages_as_pdf


# ──────────────────────────────────────────────
# 페이지 상수
# ──────────────────────────────────────────────
A4_WIDTH = 595      # pt 단위 (논리적 좌표계)
A4_HEIGHT = 842

HEADER_HEIGHT = 90
BADGE_W = 50
BADGE_H = 20
BADGE_COLOR = "#f39c12"      # 오렌지 톤
BADGE_TEXT_COLOR = "white"


# ──────────────────────────────────────────────
# 변환 유틸리티
# ──────────────────────────────────────────────
def _pil_to_qpixmap(pil_image):
    """PIL → QPixmap (RGBA 바이트 경유)."""
    if pil_image.mode != "RGBA":
        pil_image = pil_image.convert("RGBA")
    data = pil_image.tobytes("raw", "RGBA")
    qimg = QImage(data, pil_image.width, pil_image.height, QImage.Format_RGBA8888)
    return QPixmap.fromImage(qimg)


def _create_blank_page():
    """2배 DPR 흰색 A4 QPixmap 생성."""
    scale = 2
    pixmap = QPixmap(A4_WIDTH * scale, A4_HEIGHT * scale)
    pixmap.setDevicePixelRatio(scale)
    pixmap.fill(QColor("white"))
    return pixmap


# ──────────────────────────────────────────────
# 헤더(오답시트) 그리기
# ──────────────────────────────────────────────
def _draw_answer_sheet_header(painter, header_info, margin):
    """
    페이지 상단에 오답시트 헤더 표를 그립니다.

    좌측 큰 셀: 시험지 이름 + 경로
    우측 4개 칸: 오답회차 / 채점회차 / 오답갯수 / 완성확인
    """
    user_label = header_info.get("paper_title") or header_info.get("user_label", "")
    course = header_info.get("course", "")
    textbook = header_info.get("textbook", "")
    chapter = header_info.get("chapter", "")

    x = margin
    y = margin
    total_w = A4_WIDTH - margin * 2
    h = HEADER_HEIGHT - 10

    right_cols = ["오답회차", "채점회차", "오답갯수", "완성확인"]
    right_col_w = 55
    right_total_w = right_col_w * len(right_cols)
    left_w = total_w - right_total_w

    pen = QPen(QColor("#333333"))
    pen.setWidth(1)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    # 좌측 큰 셀
    painter.drawRect(x, y, left_w, h)

    # 사용자 라벨 (큰 글자)
    painter.setFont(QFont(config.FONT_FAMILY, 14, QFont.Bold))
    painter.setPen(QColor("#222222"))
    painter.drawText(
        QRect(x + 12, y + 8, left_w - 24, 30),
        Qt.AlignLeft | Qt.AlignVCenter,
        user_label,
    )

    # 경로
    painter.setFont(QFont(config.FONT_FAMILY, 9))
    painter.setPen(QColor("#666666"))
    path_text = " > ".join([t for t in [course, textbook, chapter] if t])
    painter.drawText(
        QRect(x + 12, y + h - 30, left_w - 24, 22),
        Qt.AlignLeft | Qt.AlignVCenter,
        path_text,
    )

    # 우측 4개 칸 (헤더 + 빈 입력)
    painter.setPen(pen)
    painter.setFont(QFont(config.FONT_FAMILY, 9, QFont.Bold))
    header_h = 22
    for i, col in enumerate(right_cols):
        cx = x + left_w + i * right_col_w
        # 헤더
        painter.setBrush(QColor("#f5f7fa"))
        painter.drawRect(cx, y, right_col_w, header_h)
        painter.setPen(QColor("#333333"))
        painter.drawText(
            QRect(cx, y, right_col_w, header_h),
            Qt.AlignCenter,
            col,
        )
        # 입력 영역
        painter.setBrush(Qt.NoBrush)
        painter.setPen(pen)
        painter.drawRect(cx, y + header_h, right_col_w, h - header_h)


# ──────────────────────────────────────────────
# 문제 번호 뱃지
# ──────────────────────────────────────────────
def _draw_problem_badge(painter, x, y, number_text):
    """이미지 위에 둥근 사각형 + 번호 텍스트 뱃지를 그립니다."""
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(QColor(BADGE_COLOR)))
    painter.drawRoundedRect(x, y, BADGE_W, BADGE_H, 4, 4)

    painter.setPen(QColor(BADGE_TEXT_COLOR))
    painter.setFont(QFont(config.FONT_FAMILY, 9, QFont.Bold))
    painter.drawText(
        QRect(x, y, BADGE_W, BADGE_H),
        Qt.AlignCenter,
        number_text,
    )
    painter.restore()


# ──────────────────────────────────────────────
# 페이지 빌더 (basic / horizontal)
# ──────────────────────────────────────────────
def create_note_pages(
    image_paths,
    problem_num: bool = True,
    is_horizontal: bool = False,
    margin: int = 50,
    spacing: int = 15,
    header_info: dict = None,
    include_answer_sheet: bool = False,
):
    """
    이미지 경로 리스트를 A4 QPixmap 페이지 리스트로 렌더링.

    Args:
        image_paths: list[Path | str] 문제 이미지
        problem_num: 문제 번호 뱃지 표시 여부
        is_horizontal: True면 2단 가로장형 레이아웃
        margin: 페이지 외부 여백 (10~200)
        spacing: 문제 간 세로 간격 (0~100)
        header_info: 오답시트 헤더에 들어갈 정보
        include_answer_sheet: 첫 페이지에 헤더 표시 여부
    """
    if not image_paths:
        return []

    margin = max(5, min(200, int(margin)))
    spacing = max(0, min(1000, int(spacing)))
    cols = 2 if is_horizontal else 1
    inner_gap = max(6, spacing // 2 + 4) if cols == 2 else 0

    content_w = A4_WIDTH - margin * 2
    if cols == 2:
        col_w = (content_w - inner_gap) // 2
    else:
        col_w = content_w

    pages = []

    def _new_page(is_first):
        pixmap = _create_blank_page()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.Antialiasing)
        start_y = margin
        if is_first and include_answer_sheet and header_info:
            _draw_answer_sheet_header(painter, header_info, margin)
            start_y = margin + HEADER_HEIGHT
        return pixmap, painter, start_y

    current_page, painter, page_top = _new_page(is_first=True)
    # 컬럼별 진행 y좌표
    col_y = [page_top] * cols
    col_idx = 0

    badge_offset = 22 if problem_num else 0   # 뱃지 + 약간의 간격

    for img_path in image_paths:
        img_path = Path(img_path)
        try:
            img = Image.open(str(img_path))
        except Exception:
            continue
        img_w, img_h = img.size

        # 컬럼 너비에 맞춰 비율 축소
        scale = col_w / img_w
        scaled_w = int(img_w * scale)
        scaled_h = int(img_h * scale)

        block_h = scaled_h + badge_offset

        # 페이지 안에 못 들어가면 다음 컬럼/페이지로 이동
        if col_y[col_idx] + block_h > A4_HEIGHT - margin:
            col_idx += 1
            if col_idx >= cols:
                # 페이지 마감 후 새 페이지
                painter.end()
                pages.append(current_page)
                current_page, painter, page_top = _new_page(is_first=False)
                col_y = [page_top] * cols
                col_idx = 0

        x = margin + col_idx * (col_w + inner_gap)
        y = col_y[col_idx]

        # 번호 뱃지
        if problem_num:
            number_text = img_path.stem
            _draw_problem_badge(painter, x, y, number_text)

        # 이미지
        qpixmap = _pil_to_qpixmap(img)
        painter.drawPixmap(
            x, y + badge_offset,
            scaled_w, scaled_h,
            qpixmap,
        )

        col_y[col_idx] += block_h + spacing

    painter.end()
    pages.append(current_page)
    return pages


# ──────────────────────────────────────────────
# 다이얼로그 전용 스타일
# ──────────────────────────────────────────────
_TOOLBAR_FRAME = f"""
    QFrame#previewToolbar {{
        background-color: {S.BG_CARD};
        border-bottom: 1px solid {S.BORDER};
    }}
"""

_NAV_BTN = f"""
    QPushButton {{
        background-color: {S.BG_INPUT};
        color: {S.TEXT_SECONDARY};
        border: 1px solid {S.BORDER};
        border-radius: 4px;
        font-size: 16px;
        font-weight: bold;
        padding: 4px 10px;
    }}
    QPushButton:hover {{ background-color: {S.BG_HOVER}; color: {S.TEXT_PRIMARY}; }}
    QPushButton:disabled {{ color: {S.TEXT_DISABLED}; background-color: {S.BG_DISABLED}; }}
"""

_TOOLBAR_LABEL = f"color: {S.TEXT_SECONDARY}; font-size: 13px;"

_SPINBOX = f"""
    QSpinBox {{
        border: 1px solid {S.BORDER};
        border-radius: 4px;
        padding: 4px 6px;
        background-color: {S.BG_CARD};
        color: {S.TEXT_PRIMARY};
        font-size: 13px;
        min-width: 60px;
    }}
    QSpinBox:focus {{ border: 1px solid {S.PRIMARY}; }}
"""

_BTN_OUTLINE = f"""
    QPushButton {{
        background-color: {S.BG_CARD};
        color: {S.TEXT_SECONDARY};
        border: 1px solid {S.BORDER};
        border-radius: 5px;
        font-size: 14px;
        font-weight: bold;
        padding: 8px 16px;
    }}
    QPushButton:hover {{ background-color: {S.BG_HOVER}; color: {S.TEXT_PRIMARY}; }}
"""

_BTN_TOGGLE_ON = f"""
    QPushButton {{
        background-color: {S.PRIMARY_LIGHT};
        color: {S.PRIMARY};
        border: 1.5px solid {S.PRIMARY};
        border-radius: 5px;
        font-size: 14px;
        font-weight: bold;
        padding: 8px 16px;
    }}
    QPushButton:hover {{ background-color: {S.PRIMARY_LIGHT}; }}
"""

_BTN_PRINT_COMPACT = f"""
    QPushButton {{
        background-color: {S.PRIMARY};
        color: white;
        border: none;
        border-radius: 5px;
        font-weight: bold;
        font-size: 14px;
        padding: 8px 16px;
    }}
    QPushButton:hover {{ background-color: {S.PRIMARY_DARK}; }}
"""

_BTN_SAVE_COMPACT = f"""
    QPushButton {{
        background-color: {S.GREEN};
        color: white;
        border: none;
        border-radius: 5px;
        font-weight: bold;
        font-size: 14px;
        padding: 8px 16px;
    }}
    QPushButton:hover {{ background-color: {S.GREEN_DARK}; }}
"""

_PREVIEW_AREA = f"""
    QScrollArea {{
        border: none;
        background-color: {S.BG_BODY};
    }}
    QScrollArea > QWidget > QWidget {{
        background-color: {S.BG_BODY};
    }}
"""


# ──────────────────────────────────────────────
# NotePreviewDialog
# ──────────────────────────────────────────────
class NotePreviewDialog(QDialog):
    """오답노트 미리보기 다이얼로그 (출력/PDF 저장 포함)."""

    PREVIEW_WIDTH = 880

    def __init__(self, image_paths, header_info, parent=None):
        super().__init__(parent)
        self.image_paths = list(image_paths) if image_paths else []
        self.header_info = header_info or {}

        self.margin = int(self.header_info.get("margin", 10))
        self.spacing = int(self.header_info.get("spacing", 15))
        self.include_answer_sheet = bool(self.header_info.get("include_answer_sheet", True))
        self.note_format = self.header_info.get("format", "horizontal")
        self.problem_num = bool(self.header_info.get("problem_num", True))
        self.paper_title = str(self.header_info.get("paper_title", ""))

        self.current_page = 0
        self.pages = []

        # 입력값 변경 후 짧게 디바운스하여 재렌더
        self._rerender_timer = QTimer(self)
        self._rerender_timer.setSingleShot(True)
        self._rerender_timer.setInterval(180)
        self._rerender_timer.timeout.connect(self._rerender)

        self.setWindowTitle("미리보기 - 오답노트")
        self.resize(1200, 1150)
        self.setStyleSheet(f"QDialog {{ background-color: {S.BG_BODY}; }}")

        self._init_ui()
        self._rerender()

    # ──────────────────────────────────────────────
    # UI 구성
    # ──────────────────────────────────────────────
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_title_bar())
        layout.addWidget(self._build_toolbar())
        layout.addWidget(self._build_preview_area(), 1)

    def _build_title_bar(self):
        bar = QFrame()
        bar.setObjectName("paperTitleBar")
        bar.setFixedHeight(52)
        bar.setStyleSheet(
            f"QFrame#paperTitleBar {{"
            f" background-color: {S.BG_CARD};"
            f" border-bottom: 1px solid {S.BORDER};"
            f" }}"
        )

        row = QHBoxLayout(bar)
        row.setContentsMargins(16, 8, 16, 8)
        row.setSpacing(10)

        label = QLabel("시험지 이름")
        label.setStyleSheet(f"color: {S.TEXT_SECONDARY}; font-size: 14px; font-weight: bold;")
        row.addWidget(label)

        self.title_edit = QLineEdit()
        self.title_edit.setText(self.paper_title)
        self.title_edit.setPlaceholderText("시험지 이름을 입력하세요")
        self.title_edit.setStyleSheet(
            f"QLineEdit {{"
            f" border: 1px solid {S.BORDER};"
            f" border-radius: 4px;"
            f" padding: 6px 10px;"
            f" background-color: {S.BG_CARD};"
            f" color: {S.TEXT_PRIMARY};"
            f" font-size: 14px;"
            f" }}"
            f"QLineEdit:focus {{ border: 1px solid {S.PRIMARY}; }}"
        )
        self.title_edit.textChanged.connect(self._on_title_changed)
        row.addWidget(self.title_edit, 1)

        return bar

    def _build_toolbar(self):
        toolbar = QFrame()
        toolbar.setObjectName("previewToolbar")
        toolbar.setFixedHeight(70)
        toolbar.setStyleSheet(_TOOLBAR_FRAME)

        row = QHBoxLayout(toolbar)
        row.setContentsMargins(16, 10, 16, 10)
        row.setSpacing(10)

        # 페이지 네비
        self.page_info_label = QLabel("미리보기 0/0페이지")
        self.page_info_label.setStyleSheet(_TOOLBAR_LABEL)
        row.addWidget(self.page_info_label)

        self.prev_btn = QPushButton("◀")
        self.prev_btn.setFixedSize(36, 32)
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.setStyleSheet(_NAV_BTN)
        self.prev_btn.clicked.connect(self._prev_page)
        row.addWidget(self.prev_btn)

        self.next_btn = QPushButton("▶")
        self.next_btn.setFixedSize(36, 32)
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setStyleSheet(_NAV_BTN)
        self.next_btn.clicked.connect(self._next_page)
        row.addWidget(self.next_btn)

        row.addSpacing(12)
        row.addWidget(self._vertical_divider())
        row.addSpacing(12)

        # 여백
        margin_label = QLabel("여백")
        margin_label.setStyleSheet(_TOOLBAR_LABEL)
        row.addWidget(margin_label)

        self.margin_spin = QSpinBox()
        self.margin_spin.setRange(5, 200)
        self.margin_spin.setValue(self.margin)
        self.margin_spin.setSuffix(" px")
        self.margin_spin.setStyleSheet(_SPINBOX)
        self.margin_spin.valueChanged.connect(self._on_margin_changed)
        row.addWidget(self.margin_spin)

        # 간격
        spacing_label = QLabel("간격")
        spacing_label.setStyleSheet(_TOOLBAR_LABEL)
        row.addWidget(spacing_label)

        self.spacing_spin = QSpinBox()
        self.spacing_spin.setRange(0, 1000)
        self.spacing_spin.setSingleStep(10)
        self.spacing_spin.setValue(self.spacing)
        self.spacing_spin.setSuffix(" px")
        self.spacing_spin.setStyleSheet(_SPINBOX)
        self.spacing_spin.valueChanged.connect(self._on_spacing_changed)
        row.addWidget(self.spacing_spin)

        row.addStretch(1)

        # 우측 액션 버튼
        self.sheet_btn = QPushButton("오답시트")
        self.sheet_btn.setCursor(Qt.PointingHandCursor)
        self.sheet_btn.setCheckable(True)
        self.sheet_btn.setChecked(self.include_answer_sheet)
        self.sheet_btn.clicked.connect(self._on_toggle_sheet)
        self._apply_sheet_btn_style()
        row.addWidget(self.sheet_btn)

        self.print_btn = QPushButton("출력")
        self.print_btn.setCursor(Qt.PointingHandCursor)
        self.print_btn.setStyleSheet(_BTN_PRINT_COMPACT)
        self.print_btn.clicked.connect(self._on_print)
        row.addWidget(self.print_btn)

        self.save_btn = QPushButton("파일 저장")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet(_BTN_SAVE_COMPACT)
        self.save_btn.clicked.connect(self._on_save_pdf)
        row.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet(_BTN_OUTLINE)
        self.cancel_btn.clicked.connect(self.reject)
        row.addWidget(self.cancel_btn)

        return toolbar

    def _vertical_divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setStyleSheet(f"color: {S.BORDER}; background-color: {S.BORDER};")
        line.setFixedWidth(1)
        return line

    def _build_preview_area(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignCenter)
        scroll.setStyleSheet(_PREVIEW_AREA)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        container_layout.setContentsMargins(12, 8, 12, 12)

        self.page_label = QLabel()
        self.page_label.setAlignment(Qt.AlignCenter)
        self.page_label.setStyleSheet(
            f"background-color: white; border: 1px solid {S.BORDER};"
        )
        container_layout.addWidget(self.page_label, 0, Qt.AlignHCenter)

        scroll.setWidget(container)
        return scroll

    def _apply_sheet_btn_style(self):
        if self.sheet_btn.isChecked():
            self.sheet_btn.setStyleSheet(_BTN_TOGGLE_ON)
        else:
            self.sheet_btn.setStyleSheet(_BTN_OUTLINE)

    # ──────────────────────────────────────────────
    # 렌더링
    # ──────────────────────────────────────────────
    def _rerender(self):
        is_horizontal = self.note_format == "horizontal"
        render_header = {**self.header_info, "paper_title": self.paper_title}
        self.pages = create_note_pages(
            self.image_paths,
            problem_num=self.problem_num,
            is_horizontal=is_horizontal,
            margin=self.margin,
            spacing=self.spacing,
            header_info=render_header,
            include_answer_sheet=self.include_answer_sheet,
        )
        if self.current_page >= len(self.pages):
            self.current_page = max(0, len(self.pages) - 1)
        self._update_page()

    def _update_page(self):
        total = len(self.pages)
        if total == 0:
            self.page_label.clear()
            self.page_info_label.setText("미리보기 0/0페이지")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return

        pixmap = self.pages[self.current_page]
        # 라벨 폭에 맞춰 비례 축소
        target_w = self.PREVIEW_WIDTH
        target_h = int(target_w * A4_HEIGHT / A4_WIDTH)
        scaled = pixmap.scaled(
            QSize(target_w, target_h),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.page_label.setPixmap(scaled)
        self.page_label.setFixedSize(scaled.size())

        self.page_info_label.setText(
            f"미리보기 {self.current_page + 1}/{total}페이지"
        )
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < total - 1)

    # ──────────────────────────────────────────────
    # 시그널 핸들러
    # ──────────────────────────────────────────────
    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._update_page()

    def _next_page(self):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self._update_page()

    def _on_margin_changed(self, value):
        self.margin = int(value)
        self._rerender_timer.start()

    def _on_spacing_changed(self, value):
        self.spacing = int(value)
        self._rerender_timer.start()

    def _on_title_changed(self, text):
        self.paper_title = text
        self._rerender_timer.start()

    def _on_toggle_sheet(self):
        self.include_answer_sheet = self.sheet_btn.isChecked()
        self._apply_sheet_btn_style()
        self._rerender()

    def _on_print(self):
        if not self.pages:
            QMessageBox.warning(self, "출력 실패", "출력할 페이지가 없습니다.")
            return

        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPrinter.A4)

        dlg = QPrintDialog(printer, self)
        dlg.setWindowTitle("출력")
        if dlg.exec_() != QPrintDialog.Accepted:
            return

        painter = QPainter(printer)
        if not painter.isActive():
            QMessageBox.warning(self, "출력 실패", "프린터를 사용할 수 없습니다.")
            return

        try:
            for i, page_pixmap in enumerate(self.pages):
                if i > 0:
                    printer.newPage()
                rect = painter.viewport()
                target = page_pixmap.scaled(
                    rect.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                x = (rect.width() - target.width()) // 2
                y = (rect.height() - target.height()) // 2
                painter.drawPixmap(x, y, target)
        finally:
            painter.end()

    def _on_save_pdf(self):
        if not self.pages:
            QMessageBox.warning(self, "저장 실패", "저장할 페이지가 없습니다.")
            return

        default_name = self._build_default_filename()
        default_dir = config.DEFAULT_SAVE_LOCATION
        default_path = str(Path(default_dir) / default_name)

        path, _ = QFileDialog.getSaveFileName(
            self,
            "PDF로 저장",
            default_path,
            "PDF Files (*.pdf)",
        )
        if not path:
            return

        path_obj = Path(path)
        if path_obj.suffix.lower() != ".pdf":
            path_obj = path_obj.with_suffix(".pdf")

        try:
            ok = save_pages_as_pdf(self.pages, path_obj)
        except Exception as exc:
            QMessageBox.warning(self, "저장 실패", f"PDF 저장 중 오류가 발생했습니다.\n{exc}")
            return

        if ok:
            QMessageBox.information(
                self,
                "저장 완료",
                f"PDF로 저장되었습니다.\n{path_obj}",
            )
        else:
            QMessageBox.warning(self, "저장 실패", "PDF 파일을 만들지 못했습니다.")

    def _build_default_filename(self):
        parts = [
            self.header_info.get("course"),
            self.header_info.get("textbook"),
            self.header_info.get("chapter"),
        ]
        parts = [p for p in parts if p]
        if parts:
            base = "_".join(parts)
        else:
            base = "오답노트"
        # 파일명에 부적합한 문자 정리
        for ch in '<>:"/\\|?*':
            base = base.replace(ch, "_")
        return f"{base}.pdf"
