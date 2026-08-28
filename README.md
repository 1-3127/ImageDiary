# ImageDiary

ImageDiary는 작업 세션 시작 화면을 즉시 캡처하고 선택한 주기로 화면을 자동 캡처한 뒤, 세션 종료 시 시간순 Animated GIF를 만드는 Windows 데스크톱 프로그램입니다.

## 현재 상태

v0.4 안전장치 구현을 진행 중입니다. v0.3 실사용 테스트에서 확인된 복구·내보내기 오류 흐름을 보완하고 있습니다.

- PySide6 기반 최소 UI
- 5~30분 범위의 5분 단위 캡처 간격
- 시작 즉시 캡처 후 시스템 시계 경계 기반 스케줄링
- 첫 이미지와 마지막 이미지 수정 시각을 사용하는 `Diary_HHMM-HHMM.gif` 파일명
- `001`, `002`, `003` 순번 이미지 즉시 저장
- 종료 및 저장 시 내보내기 설정 팝업
- 내보내기 설정: 내보내기 위치, 전체 블러, 상·하단 50px 마스킹, 반복 워터마크, 타임코드
- GIF 없이 원본 이미지만 내보내기 및 출력 설정 기억하기
- 완료 후 결과 폴더 열기
- `C:\temp\workdiary` 내부 원본 기반 미완료 세션 복구 및 `.unfin` 마커 보관
- 미완료 세션 GIF 재시도와 내부 원본이 남은 완료 세션의 GIF 재생성
- GIF·원본 이미지의 개별 저장 경로와 원본 이미지 저장 토글
- PNG/WebP/JPG 저장 포맷과 품질 설정
- 항상 위에 고정, Windows 로그인 시작, GIF 진행 팝업
- 최근 수정 세션 2개 보호 및 생성 날짜 기준 7일 이상 내부 원본 자동 정리

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

내부 원본은 `C:\temp\workdiary`에 저장됩니다. 최근 수정 세션 2개는 항상 보호되며, 나머지는 세션 생성 날짜로부터 7일이 지나면 자동 정리됩니다. GIF와 원본 이미지의 내보내기 위치는 종료 및 저장 후 열리는 내보내기 설정에서 선택합니다. GIF 저장을 취소해 종료하거나 실패한 세션은 `.unfin` 마커로 보관하며 설정 창에서 다시 내보낼 수 있습니다.

## MVP 범위 제외

세션 목록, 통합 결과 미리보기, DB 및 AI 분석은 후속 버전에서 검토합니다.

## Windows 패키징

PyInstaller 빌드 의존성을 설치한 뒤 저장소 root에서 실행합니다.

```powershell
.\WIP\.venv\Scripts\python.exe -m pip install -r .\WIP\requirements-build.txt
.\WIP\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm --distpath .\Release --workpath .\build\pyinstaller .\packaging\ImageDiary.spec
```

결과물은 `Release\ImageDiary-v0.3\ImageDiary.exe`에 생성됩니다.
