"""
위젯 스타일 관리 - 모든 QSS 스타일과 폰트 크기를 한곳에서 관리합니다.

사용법:
    from src.ui.widget_style import Style
    widget.setStyleSheet(Style.SIDEBAR)
"""

import config

# ──────────────────────────────────────────────
# 색상 팔레트 (여기만 바꾸면 전체 테마가 변경됩니다)
# ──────────────────────────────────────────────
PRIMARY = "#2541b2"
PRIMARY_DARK = "#1e3699"
PRIMARY_DARKER = "#172a7a"
PRIMARY_LIGHT = "#e8ecf8"
PRIMARY_GRADIENT_START = "#1b3280"
PRIMARY_GRADIENT_END = "#2d4fc7"

GREEN = "#34a853"
GREEN_DARK = "#2d8e47"
RED_CLOSE = "#c0392b"                      # 닫기 버튼 hover (딥블루에 어울리는 톤)
CTRL_BTN_HOVER = "rgba(255,255,255,0.15)"  # 최소화/최대화 hover

BG_BODY = "#f5f7fa"
BG_CARD = "white"
BG_INPUT = "#f5f7fa"
BG_HOVER = "#e8eaed"
BG_DISABLED = "#f0f0f0"

BORDER = "#e0e0e0"
BORDER_LIGHT = "#e8e8e8"
BORDER_SEPARATOR = "#e8eaed"

TEXT_PRIMARY = "#333"
TEXT_SECONDARY = "#555"
TEXT_MUTED = "#666"
TEXT_PLACEHOLDER = "#888"
TEXT_DISABLED = "#bbb"

# ──────────────────────────────────────────────
# 폰트 크기 (px 단위, 모두 QSS에서 사용)
# ──────────────────────────────────────────────
FONT_PX_TITLE_BAR = 29         # 타이틀바 앱 이름
FONT_PX_SECTION_TITLE = 28     # 사이드바 섹션 제목 ("Root dir")
FONT_PX_MAIN_TITLE = 28        # 메인 영역 제목 ("문제 선택")
FONT_PX_COMBO = 24            # 콤보박스 텍스트
FONT_PX_MENU_ITEM = 22        # 드롭다운 메뉴 아이템
FONT_PX_BUTTON = 28           # 버튼 텍스트
FONT_PX_TOOLBAR_BTN = 25      # 전체선택/해제 버튼
FONT_PX_BADGE = 22            # 선택됨 뱃지
FONT_PX_PATH_LABEL = 24       # 경로 표시 라벨
FONT_PX_STATUS_BAR = 27       # 상태바


# ──────────────────────────────────────────────
# 위젯별 QSS 스타일
# ──────────────────────────────────────────────

# 전체 앱 배경
MAIN_WINDOW = f"QMainWindow {{ background-color: {BG_BODY}; }}"

# 커스텀 타이틀바
HEADER = f"""
    QFrame {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {PRIMARY_GRADIENT_START}, stop:1 {PRIMARY_GRADIENT_END});
        border: none;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
    }}
"""

HEADER_TITLE = f"color: white; background: transparent; font-size: {FONT_PX_TITLE_BAR}px; font-weight: bold;"

HEADER_VERSION = "color: rgba(255,255,255,0.6); background: transparent; margin-right: 12px;"

# 창 컨트롤 버튼 (최소화/최대화) - format으로 size, hover를 채워서 사용
WINDOW_CTRL_BTN = f"""
    QPushButton {{{{
        background-color: rgba(255,255,255,0.1);
        color: rgba(255,255,255,0.85);
        border: none;
        border-radius: 4px;
        font-size: {{size}}px;
        font-weight: bold;
        padding: 0;
    }}}}
    QPushButton:hover {{{{
        background-color: {{hover}};
        color: white;
    }}}}
"""

# 사이드바 프레임
SIDEBAR = f"""
    QFrame#sidebar {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: 8px;
    }}
"""

# 사이드바 섹션 제목 라벨
SECTION_LABEL = f"color: {TEXT_PRIMARY}; border: none; font-size: {FONT_PX_SECTION_TITLE}px; font-weight: bold;"

# 루트 경로 표시 라벨
PATH_LABEL = f"""
    QLabel {{
        color: {TEXT_PLACEHOLDER};
        padding: 8px 10px;
        border: none;
        background-color: {BG_INPUT};
        border-radius: 6px;
        font-size: {FONT_PX_PATH_LABEL}px;
    }}
"""

# 폴더 선택 버튼 (Primary 강조)
BTN_PRIMARY = f"""
    QPushButton {{
        background-color: {PRIMARY};
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: bold;
        font-size: {FONT_PX_BUTTON}px;
    }}
    QPushButton:hover {{
        background-color: {PRIMARY_DARK};
    }}
    QPushButton:pressed {{
        background-color: {PRIMARY_DARKER};
    }}
"""

# 설정 버튼 (Secondary)
BTN_SECONDARY = f"""
    QPushButton {{
        background-color: {BG_INPUT};
        color: {TEXT_SECONDARY};
        border: 1px solid {BORDER};
        border-radius: 6px;
        font-size: {FONT_PX_BUTTON}px;
    }}
    QPushButton:hover {{
        background-color: {BG_HOVER};
        color: {TEXT_PRIMARY};
    }}
"""

# 콤보박스
COMBOBOX = f"""
    QComboBox {{
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 8px 30px 8px 12px;
        background-color: {BG_INPUT};
        color: {TEXT_PRIMARY};
        font-size: {FONT_PX_COMBO}px;
    }}
    QComboBox:hover {{
        border: 1px solid {PRIMARY};
        background-color: {PRIMARY_LIGHT};
    }}
    QComboBox:disabled {{
        background-color: {BG_DISABLED};
        color: {TEXT_DISABLED};
        border: 1px solid {BORDER_LIGHT};
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: center right;
        width: 30px;
        border: none;
    }}
    QComboBox::down-arrow {{
        image: none;
        border: none;
        width: 0;
        height: 0;
    }}
"""

# 콤보박스 드롭다운 메뉴
COMBOBOX_MENU = f"""
    QMenu {{
        background-color: white;
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 6px 0;
    }}
    QMenu::item {{
        padding: 8px 24px;
        font-size: {FONT_PX_MENU_ITEM}px;
        color: {TEXT_PRIMARY};
    }}
    QMenu::item:selected {{
        background-color: {PRIMARY_LIGHT};
        color: {PRIMARY};
    }}
"""

# 메인 영역 프레임
MAIN_AREA = f"""
    QFrame#mainArea {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: 8px;
    }}
"""

# 메인 영역 제목 라벨
MAIN_TITLE = f"color: {TEXT_PRIMARY}; border: none; background-color: white; font-size: {FONT_PX_MAIN_TITLE}px; font-weight: bold;"

# 선택됨 뱃지
SELECTION_BADGE = f"""
    color: white;
    background-color: {PRIMARY};
    border: none;
    border-radius: 10px;
    padding: 4px 12px;
    font-size: {FONT_PX_BADGE}px;
    font-weight: bold;
"""

# 전체선택/해제 버튼
BTN_TOOLBAR = f"""
    QPushButton {{
        background-color: {BG_INPUT};
        color: {TEXT_SECONDARY};
        border: 1px solid {BORDER};
        border-radius: 5px;
        padding: 5px 14px;
        font-size: {FONT_PX_TOOLBAR_BTN}px;
    }}
    QPushButton:hover {{
        background-color: {BG_HOVER};
        color: {TEXT_PRIMARY};
    }}
"""

# 문제 목록 스크롤 영역
PROBLEM_LIST = f"""
    QScrollArea {{
        border: 1px solid {BORDER};
        border-radius: 6px;
        background-color: #fafbfc;
    }}
    QScrollArea > QWidget > QWidget {{
        background-color: #fafbfc;
    }}
"""

# 문제 개별 체크박스
PROBLEM_ITEM = f"""
    QCheckBox {{
        padding: 10px 8px;
        color: {TEXT_PRIMARY};
        spacing: 6px;
    }}
    QCheckBox:hover {{
        background-color: {PRIMARY_LIGHT};
        border-radius: 4px;
    }}
"""

# 액션 버튼 - 미리보기 (아웃라인)
BTN_PREVIEW = f"""
    QPushButton {{
        background-color: {BG_INPUT};
        color: {PRIMARY};
        border: 2px solid {PRIMARY};
        border-radius: 6px;
        font-weight: bold;
        font-size: {FONT_PX_BUTTON}px;
    }}
    QPushButton:hover {{ background-color: {PRIMARY_LIGHT}; }}
"""

# 액션 버튼 - 출력 (Primary)
BTN_PRINT = f"""
    QPushButton {{
        background-color: {PRIMARY};
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: bold;
        font-size: {FONT_PX_BUTTON}px;
    }}
    QPushButton:hover {{ background-color: {PRIMARY_DARK}; }}
"""

# 액션 버튼 - 저장 (Green)
BTN_SAVE = f"""
    QPushButton {{
        background-color: {GREEN};
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: bold;
        font-size: {FONT_PX_BUTTON}px;
    }}
    QPushButton:hover {{ background-color: {GREEN_DARK}; }}
"""

# 상태바
STATUS_BAR = f"""
    QStatusBar {{
        background-color: {BG_BODY};
        color: {TEXT_MUTED};
        border-top: 1px solid {BORDER};
        padding: 4px 12px;
        font-size: {FONT_PX_STATUS_BAR}px;
    }}
"""

# 구분선
SEPARATOR = f"background-color: {BORDER_SEPARATOR}; border: none;"
