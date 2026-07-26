#!/usr/bin/env bash
# macOS 빌드 스크립트 (클라우드 Mac / 실제 Mac 공통)
#   사용법:  chmod +x build_mac.sh && ./build_mac.sh
#   결과물:  dist/QBank.app  →  QBank-macos.zip 로 압축
set -euo pipefail

echo "==> Python / pip 버전"
python3 --version
python3 -m pip --version

echo "==> 가상환경 생성 및 의존성 설치"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "==> PyInstaller 빌드 (QBank.spec, macOS면 .icns 자동 선택)"
pyinstaller --noconfirm --clean QBank.spec

echo "==> .app 압축 (심볼릭 링크 보존을 위해 -y)"
cd dist
zip -r -y ../QBank-macos.zip QBank.app
cd ..

echo "==> 완료: dist/QBank.app 및 QBank-macos.zip 생성"
ls -la dist
