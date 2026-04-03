# SAMPAS
**Simulation-Aided Material & Processes Analysis System**

## 프로젝트 구조

```
SAMPAS/
├── main.py                    # 실행 진입점
├── setup.py
├── requirements.txt
├── SAMPAS.spec                # PyInstaller 빌드 설정
├── SAMPAS_installer.iss       # Inno Setup 인스톨러 스크립트
├── build_windows.bat          # 원클릭 빌드 스크립트
└── sampas/
    ├── __init__.py
    ├── app.py                 # 메인 GUI (tkinter)
    └── modules/
        ├── __init__.py
        ├── pyAEP.py           # 흡착 공정 모듈
        └── pySembrane.py      # 분리막 공정 모듈
```

## 실행 (개발 환경)

```bash
pip install numpy
python main.py
```

## Windows 인스톨러 빌드

→ README_BUILD.md 참조
