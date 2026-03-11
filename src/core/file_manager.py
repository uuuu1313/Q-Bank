"""
파일 매니저 - 수학 문제 폴더 구조를 탐색하는 클래스

폴더 구조:
    루트디렉토리/
        [과정명]/           예: 고등학교 수학
            [교재명]/       예: 개념쎈 수학I
                [단원명]/   예: 집합
                    문제01.png
                    문제02.png
"""

from pathlib import Path
from typing import List

import config


class FileManager:
    """폴더 계층 구조를 탐색하여 과정/교재/단원/문제를 반환합니다."""

    def __init__(self, root_path: str = None):
        # 루트 경로가 주어지면 사용, 아니면 config의 기본값 사용
        if root_path:
            self.root = Path(root_path)
        else:
            self.root = config.USER_DATA_ROOT

    def set_root(self, root_path: str):
        """루트 디렉토리를 변경합니다."""
        self.root = Path(root_path)

    def get_root(self) -> str:
        """현재 루트 디렉토리 경로를 반환합니다."""
        return str(self.root)

    def is_valid_root(self) -> bool:
        """루트 디렉토리가 존재하는지 확인합니다."""
        return self.root.exists() and self.root.is_dir()

    def _get_subdirs(self, path: Path) -> List[str]:
        """주어진 경로의 하위 폴더 이름 목록을 반환합니다. (공통 로직)"""
        if not path.exists() or not path.is_dir():
            return []
        return sorted([
            d.name for d in path.iterdir()
            if d.is_dir() and not d.name.startswith('.')
        ])

    def get_courses(self) -> List[str]:
        """과정 목록을 반환합니다. (루트 바로 아래 폴더들)"""
        if not self.is_valid_root():
            return []
        return self._get_subdirs(self.root)

    def get_textbooks(self, course: str) -> List[str]:
        """선택한 과정의 교재 목록을 반환합니다."""
        return self._get_subdirs(self.root / course)

    def get_chapters(self, course: str, textbook: str) -> List[str]:
        """선택한 교재의 단원 목록을 반환합니다."""
        return self._get_subdirs(self.root / course / textbook)

    def get_problems(self, course: str, textbook: str, chapter: str) -> List[str]:
        """선택한 단원의 문제 이미지 파일 목록을 반환합니다."""
        path = self.root / course / textbook / chapter
        if not path.exists() or not path.is_dir():
            return []
        # config에 정의된 이미지 확장자만 필터링 (.png, .jpg, .jpeg)
        extensions = {ext.lower() for ext in config.SUPPORTED_IMAGE_FORMATS}
        return sorted([
            f.name for f in path.iterdir()
            if f.is_file() and f.suffix.lower() in extensions
        ])

    def get_problem_path(self, course: str, textbook: str, chapter: str, problem: str) -> Path:
        """문제 이미지의 전체 경로를 반환합니다."""
        return self.root / course / textbook / chapter / problem
