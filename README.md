# ImageDiary

ImageDiary는 작업 세션 시작 화면을 즉시 캡처하고 선택한 주기로 화면을 자동 캡처한 뒤, 세션 종료 시 시간순 Animated GIF를 만드는 Windows 데스크톱 프로그램입니다.

## 현재 상태

v0.2의 구현, 자동 검증 및 핵심 Windows 실환경 검증을 완료했습니다.

- PySide6 기반 최소 UI
- 10~30분 범위의 5분 단위 캡처 간격과 1분 디버그 모드
- 시작 즉시 캡처 후 시스템 시계 경계 기반 스케줄링
- 첫 이미지와 마지막 이미지 수정 시각을 사용하는 `Diary_HHMM-HHMM.gif` 파일명
- `001`, `002`, `003` 순번 이미지 즉시 저장
- Finish 시 단일 GIF 생성
- 완료 후 결과 폴더 열기
- `C:\temp\workdiary` 내부 원본 기반 미완료 세션 복구
- 사용자 지정 단일 저장 경로와 종료 시 Screenshot 전체 복사 토글
- PNG/WebP/JPG 저장 포맷과 품질 설정
- 항상 위에 고정, Windows 로그인 시작, GIF 진행 팝업
- 최근 수정 세션 2개 보호 및 나머지 7일 이상 내부 원본 자동 정리

구현 계획은 [Plan/versioned_implementation_plan.md](Plan/versioned_implementation_plan.md)에서 확인할 수 있습니다.

## 프로젝트 구조

```text
ImageDiary/
├─ Plan/
│  └─ versioned_implementation_plan.md
└─ WIP/
   ├─ main.py
   ├─ app.py
   ├─ session_controller.py
   ├─ capture_scheduler.py
   ├─ screenshot_capture.py
   ├─ gif_builder.py
   ├─ image_order.py
   ├─ file_exporter.py
   ├─ data_cleanup.py
   ├─ retention.py
   ├─ session_recovery.py
   ├─ recovery_dialog.py
   ├─ gif_progress_dialog.py
   ├─ session_status_widget.py
   ├─ settings_dialog.py
   ├─ settings_repository.py
   ├─ startup_manager.py
   ├─ storage.py
   ├─ settings.py
   ├─ tests/
   └─ requirements.txt
```

각 기능은 독립된 Python 모듈로 분리되어 있습니다.

## 개발 환경 실행

Python 3.11 이상을 권장합니다.

```powershell
cd WIP
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python main.py
```

내부 원본은 `C:\temp\workdiary`에 저장됩니다. 최근 수정 세션 2개는 항상 보호되며, 나머지는 마지막 활동 후 7일이 지나면 자동 정리됩니다. GIF 복사본은 기본적으로 `%USERPROFILE%\Pictures\WorkDiary`에 저장되며, 설정 창에서 저장 경로와 종료 시 Screenshot 전체 복사 여부를 변경할 수 있습니다.

## MVP 범위 제외

멀티 모니터 선택, Preview, DB 및 AI 분석은 후속 버전에서 검토합니다.

## Windows 패키징

PyInstaller 빌드 의존성을 설치한 뒤 저장소 root에서 실행합니다.

```powershell
.\WIP\.venv\Scripts\python.exe -m pip install -r .\WIP\requirements-build.txt
.\WIP\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm --distpath .\Release --workpath .\build\pyinstaller .\packaging\ImageDiary.spec
```

결과물은 `Release\ImageDiary-v0.2\ImageDiary.exe`에 생성됩니다. 1분 디버그 옵션도 v0.2 패키지에 포함됩니다.
