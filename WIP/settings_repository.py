"""QSettings를 통해 사용자 설정을 영구 저장한다."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings

from settings import (
    AppSettings,
    SUPPORTED_CAPTURE_FORMATS,
    SUPPORTED_CAPTURE_INTERVAL_SECONDS,
    default_settings,
)


class SettingsRepository:
    def __init__(self, backend: QSettings | None = None) -> None:
        self._backend = backend or QSettings("ImageDiary", "ImageDiary")

    def load(self) -> AppSettings:
        defaults = default_settings()
        capture_format = str(
            self._backend.value("capture/format", defaults.capture_format)
        ).lower()
        if capture_format not in SUPPORTED_CAPTURE_FORMATS:
            capture_format = defaults.capture_format
        export_root = self._backend.value("paths/export_root", None)
        if not export_root:
            export_root = self._backend.value(
                "paths/screenshot_export_root",
                str(defaults.export_root),
            )

        capture_interval_seconds = int(
            self._backend.value(
                "capture/interval_seconds",
                defaults.capture_interval_seconds,
            )
        )
        if capture_interval_seconds not in SUPPORTED_CAPTURE_INTERVAL_SECONDS:
            capture_interval_seconds = defaults.capture_interval_seconds

        return AppSettings(
            export_root=Path(str(export_root)),
            capture_interval_seconds=capture_interval_seconds,
            capture_format=capture_format,
            image_quality=int(
                self._backend.value("capture/image_quality", defaults.image_quality)
            ),
            run_at_login=self._as_bool(
                self._backend.value("startup/run_at_login", defaults.run_at_login)
            ),
            always_on_top=self._as_bool(
                self._backend.value("window/always_on_top", defaults.always_on_top)
            ),
            internal_retention_days=int(
                self._backend.value(
                    "storage/internal_retention_days",
                    defaults.internal_retention_days,
                )
            ),
            gif_frame_duration_ms=int(
                self._backend.value(
                    "gif/frame_duration_ms",
                    defaults.gif_frame_duration_ms,
                )
            ),
            gif_loop=int(self._backend.value("gif/loop", defaults.gif_loop)),
            open_output_on_finish=self._as_bool(
                self._backend.value(
                    "window/open_output_on_finish",
                    defaults.open_output_on_finish,
                )
            ),
            export_screenshots_on_finish=self._as_bool(
                self._backend.value(
                    "export/screenshots_on_finish",
                    defaults.export_screenshots_on_finish,
                )
            ),
        )

    def save(self, settings: AppSettings) -> None:
        self._backend.setValue("paths/export_root", str(settings.export_root))
        self._backend.setValue(
            "capture/interval_seconds", settings.capture_interval_seconds
        )
        self._backend.setValue("capture/format", settings.capture_format)
        self._backend.setValue("capture/image_quality", settings.image_quality)
        self._backend.setValue("startup/run_at_login", settings.run_at_login)
        self._backend.setValue("window/always_on_top", settings.always_on_top)
        self._backend.setValue(
            "storage/internal_retention_days", settings.internal_retention_days
        )
        self._backend.setValue("gif/frame_duration_ms", settings.gif_frame_duration_ms)
        self._backend.setValue("gif/loop", settings.gif_loop)
        self._backend.setValue(
            "window/open_output_on_finish", settings.open_output_on_finish
        )
        self._backend.setValue(
            "export/screenshots_on_finish", settings.export_screenshots_on_finish
        )
        self._backend.sync()

    @staticmethod
    def _as_bool(value: object) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on"}
