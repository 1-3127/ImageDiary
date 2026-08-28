"""마커가 남은 미완료 세션을 선택해 GIF 저장을 다시 시작하는 대화상자."""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QLabel, QVBoxLayout, QWidget

from session_recovery import RecoveryCandidate, UNFINISHED_MARKER_NAME


class UnfinishedSessionsDialog(QDialog):
    def __init__(
        self,
        candidates: tuple[RecoveryCandidate, ...],
        parent: QWidget | None = None,
        title: str = "이전 세션 GIF 다시 만들기",
        description: str = "GIF를 다시 만들 세션을 선택하세요.",
        confirm_text: str = "내보내기 설정",
    ) -> None:
        super().__init__(parent)
        self._candidates = candidates
        self.setWindowTitle(title)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(description, self))
        self._sessions = QComboBox(self)
        for candidate in candidates:
            state = "미완료" if (candidate.session_directory / UNFINISHED_MARKER_NAME).is_file() else "완료"
            self._sessions.addItem(
                f"[{state}] [{candidate.session_directory.name}] [{len(candidate.image_paths)}장]",
                candidate,
            )
        layout.addWidget(self._sessions)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(confirm_text)
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("취소")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_candidate(self) -> RecoveryCandidate:
        return self._sessions.currentData()
