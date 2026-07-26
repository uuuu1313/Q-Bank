# -*- mode: python ; coding: utf-8 -*-
# 크로스플랫폼 PyInstaller 빌드 스펙 (Windows / macOS)
#
#   빌드(공통): pyinstaller --noconfirm --clean QBank.spec
#     - Windows: dist/QBank.exe          (아이콘: QB_icon.ico)
#     - macOS  : dist/QBank.app          (아이콘: QB_icon.icns)
#
#   ※ PyInstaller는 크로스 컴파일 불가 → 각 OS에서 각각 빌드해야 함.

import sys

block_cipher = None
is_mac = sys.platform == 'darwin'

# OS별 아이콘 선택 (Windows=.ico, macOS=.icns)
icon_file = 'template/icon/QB_icon.icns' if is_mac else 'template/icon/QB_icon.ico'

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    # 실행 시 필요한 리소스(폰트/스타일)와 아이콘을 앱에 포함
    # datas는 튜플이라 OS별 경로 구분자(;, :) 걱정이 없음
    datas=[
        ('src/resources', 'src/resources'),
        ('template/icon', 'template/icon'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='QBank',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                 # GUI 앱 → 콘솔/터미널 창 숨김
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,              # macOS: 빌드한 아키텍처(Intel/Apple Silicon)로 생성
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

# macOS 전용: .app 번들 생성
if is_mac:
    app = BUNDLE(
        exe,
        name='QBank.app',
        icon=icon_file,
        bundle_identifier='com.qbank.app',
        info_plist={
            'NSHighResolutionCapable': True,       # Retina 대응
            'CFBundleName': 'QBank',
            'CFBundleDisplayName': 'QBank',
            'CFBundleShortVersionString': '1.0.0',
        },
    )
