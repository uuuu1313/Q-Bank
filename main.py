"""
Math Answer Note Application
Main Entry Point
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFontDatabase, QFont
from src.ui.main_window import MainWindow
import config


def main():
    """Initialize and run the application"""
    app = QApplication(sys.argv)

    # Noto Sans KR 폰트 로드 (프로젝트에 번들링된 ttf 파일)
    font_path = str(config.RESOURCES_PATH / "fonts" / "NotoSansKR-Regular.ttf")
    font_id = QFontDatabase.addApplicationFont(font_path)

    if font_id != -1:
        app.setFont(QFont(config.FONT_FAMILY, config.FONT_SIZE))

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run application event loop
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
