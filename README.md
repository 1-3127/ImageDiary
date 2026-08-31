# ImageDiary

> 작업 과정을 가볍게 기록하고, 한 편의 GIF 작업 일기로 남기세요.

ImageDiary는 작업 세션 시작 화면을 즉시 캡처하고 선택한 주기로 화면을 자동 캡처한 뒤, 세션 종료 시 시간순 Animated GIF를 만드는 Windows 데스크톱 프로그램입니다. 캡처 원본과 GIF 후처리는 로컬 PC에서 처리됩니다.

## 현재 상태

Windows용 v0.4 릴리즈를 배포했습니다. 다운로드는 [Releases](https://github.com/1-3127/ImageDiary/releases)에서 할 수 있습니다.

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
- 최근 수정 세션 2개 보호 및 마지막 활동일·보존 세션 수·할당 용량 기준의 내부 원본 자동 정리

## 문서

- [간단 사용설명서](docs/quick_start.md)
- [정식 사용설명서](docs/user_guide.md)
- [문제 해결](docs/troubleshooting.md)
- [제품 소개 문구](docs/product_overview.md)
- [버전별 구현 기능 기록](docs/version_history.md)
- [기술 구현 계획](Plan/versioned_implementation_plan.md)

## 설치와 첫 실행

1. Releases에서 Windows ZIP을 다운로드하고 압축을 풉니다.
2. 압축을 푼 폴더 안의 `ImageDiary.exe`를 실행합니다.
3. `ImageDiary.exe`와 같은 폴더의 `_internal`은 삭제하거나 분리하지 마세요.
4. 설정에서 캡처 간격과 저장 포맷을 고른 뒤 `시작`을 누릅니다.

자세한 사용 방법은 [간단 사용설명서](docs/quick_start.md)와 [정식 사용설명서](docs/user_guide.md)를 참고하세요.

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

내부 원본은 `C:\temp\workdiary`에 저장됩니다. 기본 정책은 최근 수정 세션 2개 보호 및 마지막 활동일 7일 경과 세션 정리이며, 설정에서 보존 세션 수·할당 용량·마지막 활동일 기준을 조합할 수 있습니다. GIF와 원본 이미지의 내보내기 위치는 종료 및 저장 후 열리는 내보내기 설정에서 선택합니다. GIF 저장을 취소해 종료하거나 실패한 세션은 `.unfin` 마커로 보관하며 설정 창에서 다시 내보낼 수 있습니다.

## MVP 범위 제외

세션 목록, 통합 결과 미리보기, DB 및 AI 분석은 후속 버전에서 검토합니다.

## Windows 패키징

PyInstaller 빌드 의존성을 설치한 뒤, `.spec`의 상대 경로 기준인 `packaging` 폴더에서 실행합니다.

```powershell
.\WIP\.venv\Scripts\python.exe -m pip install -r .\WIP\requirements-build.txt
Push-Location .\packaging
..\WIP\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm --distpath ..\Release --workpath ..\build\pyinstaller-v04 .\ImageDiary.spec
Pop-Location
```

결과물은 `Release\ImageDiary-v0.4\ImageDiary.exe`에 생성됩니다. `ImageDiary.exe`만 따로 복사하지 말고, 같은 폴더의 `_internal`을 포함한 전체 폴더를 함께 배포해야 합니다.
