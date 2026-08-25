"""미완료 세션의 복구 방법을 선택하는 대화상자."""

from __future__ import annotations

from enum import Enum

from PySide6.QtWidgets import QMessageBox, QWidget

from session_recovery import RecoveryCandidate


class RecoveryAction(str, Enum):
    RESUME = "resume"
    FINISH = "finish"
    LATER = "later"


def ask_recovery_action(
    candidate: RecoveryCandidate,
    parent: QWidget | None = None,
) -> RecoveryAction:
    message = QMessageBox(parent)
    message.setWindowTitle("미완료 세션 발견")
    message.setText("정상 종료되지 않은 최신 세션을 발견했습니다.")
    message.setInformativeText(str(candidate.session_directory))
    resume_button = message.addButton("세션 복구", QMessageBox.ButtonRole.AcceptRole)
    finish_button = message.addButton("세션 마치기", QMessageBox.ButtonRole.ActionRole)
    message.addButton("나중에", QMessageBox.ButtonRole.RejectRole)
    message.exec()

    if message.clickedButton() is resume_button:
        return RecoveryAction.RESUME
    if message.clickedButton() is finish_button:
        return RecoveryAction.FINISH
    return RecoveryAction.LATER
