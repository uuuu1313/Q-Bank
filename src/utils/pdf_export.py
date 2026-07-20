"""
PDF 저장 헬퍼 - 렌더된 QPixmap 페이지들을 A4 PDF 파일로 저장합니다.

QPrinter의 PDF 출력 모드를 사용하여 추가 의존성 없이 PDF를 생성합니다.
"""

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtPrintSupport import QPrinter


def save_pages_as_pdf(pages, output_path):
    """
    QPixmap 페이지 리스트를 A4 PDF로 저장합니다.

    Args:
        pages: list[QPixmap] - 저장할 페이지들
        output_path: 출력 파일 경로 (str 또는 Path)

    Returns:
        bool - 성공 여부
    """
    if not pages:
        return False

    output_path = Path(output_path)

    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setPageSize(QPrinter.A4)
    printer.setFullPage(True)
    printer.setOutputFileName(str(output_path))

    painter = QPainter(printer)
    if not painter.isActive():
        return False

    try:
        for i, pm in enumerate(pages):
            if i > 0:
                printer.newPage()
            rect = painter.viewport()
            scaled = pm.scaled(
                rect.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            x = (rect.width() - scaled.width()) // 2
            y = (rect.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
    finally:
        painter.end()

    return output_path.exists()
