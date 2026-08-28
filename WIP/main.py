"""ImageDiary 실행 진입점."""

from __future__ import annotations

import sys

from PySide6.QtCore import QCoreApplication, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from app import MainWindow
from error_reporting import install_fatal_exception_handler
from retention import cleanup_expired_sessions
from settings_repository import SettingsRepository
from startup_manager import StartupManager


def main() -> int:
    application = QApplication(sys.argv)
    application.setQuitOnLastWindowClosed(True)
    install_fatal_exception_handler(application)
    QCoreApplication.setOrganizationName("ImageDiary")
    QCoreApplication.setApplicationName("ImageDiary")
    settings_repository = SettingsRepository()
    settings = settings_repository.load()
    cleanup_error: str | None = None
    try:
        cleanup_expired_sessions(
            settings.internal_storage_root,
            settings.internal_retention_days,
            days_enabled=settings.retention_days_enabled,
            count_enabled=settings.retention_count_enabled,
            keep_count=settings.retention_keep_count,
            size_enabled=settings.retention_size_enabled,
            max_size_mb=settings.retention_max_size_mb,
        )
    except OSError as error:
        cleanup_error = str(error)

    window = MainWindow(settings_repository, StartupManager())
    application.aboutToQuit.connect(window.shutdown)
    application.lastWindowClosed.connect(lambda: application.exit(0))
    window.show()
    QTimer.singleShot(0, window.check_for_recovery)
    if cleanup_error is not None:
        QTimer.singleShot(
            0,
            lambda: QMessageBox.warning(
                window,
                "내부 저장소 정리 실패",
                cleanup_error,
            ),
        )
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
