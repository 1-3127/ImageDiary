"""마커가 남은 미완료 세션을 선택해 GIF 저장을 다시 시작하는 대화상자."""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QLabel, QVBoxLayout, QWidget

from session_recovery import RecoveryCandidate


class UnfinishedSessionsDialog(QDialog):
    def __init__(self, candidates: tuple[RecoveryCandidate, ...], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._candidates = candidates
        self.setWindowTitle("미완료 세션")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("GIF 저장을 다시 시도할 세션을 선택하세요.", self))
        self._sessions = QComboBox(self)
        for candidate in candidates:
            self._sessions.addItem(
                f"{candidate.session_directory.name} · 이미지 {len(candidate.image_paths)}장",
                candidate,
            )
        layout.addWidget(self._sessions)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("GIF 저장 설정")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("취소")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_candidate(self) -> RecoveryCandidate:
        return self._sessions.currentData()
