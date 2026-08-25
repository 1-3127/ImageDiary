# ImageDiary

ImageDiary는 작업 세션 동안 시스템 시계의 15분 또는 30분 경계에 화면을 자동 캡처하고, 세션 종료 시 캡처 이미지를 시간순 Animated GIF로 만드는 Windows 데스크톱 프로그램입니다.

## 현재 상태

v0.1 MVP를 개발 중입니다.

- PySide6 기반 최소 UI
- 60초 디버그 및 15분/30분 캡처 간격
- 시스템 시계 경계 기반 스케줄링
- timestamp PNG 즉시 저장
- Finish 시 단일 GIF 생성
- 완료 후 결과 폴더 열기

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

기본 결과 저장 위치는 `%USERPROFILE%\Pictures\WorkDiary`입니다. 세션은 `YYMMDD[-NN]` 폴더, 스크린샷은 그 아래 `Screenshot` 폴더에 저장됩니다. Pictures 폴더를 찾을 수 없으면 `%USERPROFILE%\WorkDiary`를 사용합니다.

## MVP 범위 제외

Pause/Resume, 캡처 포맷 선택, 저장 경로 UI, 멀티 모니터 선택, Preview, DB 및 AI 분석은 후속 버전에서 검토합니다.
