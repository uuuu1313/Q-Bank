"""
Configuration file for Math Answer Note Program
"""

import os
from pathlib import Path

# Application Information
APP_NAME = "Q-Bank"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Q-Bank"

# Window Settings
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 1200
WINDOW_MIN_WIDTH = 900
WINDOW_MIN_HEIGHT = 600

# User Data Path (Default: user_data folder in project root)
PROJECT_ROOT = Path(__file__).parent

# 테스트용 DB 폴더가 존재하면 우선 사용
_TEST_DB_PATH = Path(r"C:\Users\JIUK\Desktop\math_test_db")
if _TEST_DB_PATH.exists():
    USER_DATA_ROOT = _TEST_DB_PATH
else:
    USER_DATA_ROOT = PROJECT_ROOT / "user_data"
    # Ensure user_data directory exists
    USER_DATA_ROOT.mkdir(exist_ok=True)

# File Settings
SUPPORTED_IMAGE_FORMATS = ['.png', '.jpg', '.jpeg']
DEFAULT_SAVE_LOCATION = os.path.expanduser("~/Desktop")

# PDF Settings
PDF_PAGE_SIZE = "A4"  # A4 page size
PDF_MARGIN = 50  # pixels
PDF_QUALITY = 100  # image quality percentage

# UI Settings
THEME = "light"  # light or dark
FONT_FAMILY = "Noto Sans KR"
FONT_SIZE = 10

# Application Paths
RESOURCES_PATH = PROJECT_ROOT / "src" / "resources"
STYLES_PATH = RESOURCES_PATH / "styles.qss"
ICONS_PATH = RESOURCES_PATH / "icons"
