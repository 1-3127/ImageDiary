"""사용자에게 재시도·설정 복구·버그 제보 경로를 안내한다."""

from __future__ import annotations

import sys
import traceback

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox, QWidget


ISSUE_URL = "https://github.com/1-3127/ImageDiary/issues"


def issue_report_guidance() -> str:
    return (
        "문제가 반복되면 GitHub Issue에 제보해 주세요.\n"
        f"{ISSUE_URL}\n"
        "제보에는 실행 순서, 오류 메시지, ImageDiary 버전을 포함해 주세요."
    )


def show_retry_message(parent: QWidget, title: str, message: str) -> bool:
    dialog = QMessageBox(parent)
    dialog.setIcon(QMessageBox.Icon.Warning)
    dialog.setWindowTitle(title)
    dialog.setText(message)
    dialog.setInformativeText(issue_report_guidance())
    retry = dialog.addButton("다시 시도", QMessageBox.ButtonRole.AcceptRole)
    dialog.addButton("나중에 처리", QMessageBox.ButtonRole.RejectRole)
    dialog.exec()
    return dialog.clickedButton() is retry


def install_fatal_exception_handler(application: QApplication) -> None:
    """처리되지 않은 예외를 안내한 뒤 Qt 이벤트 루프를 종료한다."""

    def handle(exception_type: type[BaseException], value: BaseException, trace: object) -> None:
        traceback.print_exception(exception_type, value, trace)
        QMessageBox.critical(
            None,
            "예상하지 못한 오류",
            f"프로그램을 종료합니다.\n\n{value}\n\n{issue_report_guidance()}",
        )
        QTimer.singleShot(0, application.quit)

    sys.excepthook = handle
