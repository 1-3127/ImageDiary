"""현재 Windows 사용자의 로그인 시작 등록을 관리한다."""

from __future__ import annotations

import sys
from pathlib import Path

import winreg


RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "ImageDiary"


class StartupRegistrationError(RuntimeError):
    """Windows 로그인 시작 설정 변경 실패."""


class StartupManager:
    def command(self) -> str:
        if getattr(sys, "frozen", False):
            return f'"{Path(sys.executable).resolve()}"'
        pythonw = Path(sys.executable).resolve().with_name("pythonw.exe")
        main_script = Path(__file__).resolve().with_name("main.py")
        return f'"{pythonw}" "{main_script}"'

    def set_enabled(self, enabled: bool) -> None:
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
                if enabled:
                    winreg.SetValueEx(
                        key,
                        VALUE_NAME,
                        0,
                        winreg.REG_SZ,
                        self.command(),
                    )
                else:
                    try:
                        winreg.DeleteValue(key, VALUE_NAME)
                    except FileNotFoundError:
                        pass
        except OSError as error:
            raise StartupRegistrationError(f"로그인 시작 설정 실패: {error}") from error
