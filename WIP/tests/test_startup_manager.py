from unittest import TestCase
from unittest.mock import MagicMock, patch

from startup_manager import RUN_KEY, VALUE_NAME, StartupManager


class StartupManagerTests(TestCase):
    @patch("startup_manager.winreg.SetValueEx")
    @patch("startup_manager.winreg.CreateKey")
    def test_registers_current_user_run_command(
        self,
        create_key: MagicMock,
        set_value: MagicMock,
    ) -> None:
        key = create_key.return_value.__enter__.return_value
        manager = StartupManager()

        manager.set_enabled(True)

        create_key.assert_called_once()
        self.assertEqual(create_key.call_args.args[1], RUN_KEY)
        self.assertEqual(set_value.call_args.args[0], key)
        self.assertEqual(set_value.call_args.args[1], VALUE_NAME)
        self.assertIn("main.py", set_value.call_args.args[4])

    @patch("startup_manager.winreg.DeleteValue", side_effect=FileNotFoundError)
    @patch("startup_manager.winreg.CreateKey")
    def test_disable_is_idempotent(
        self,
        _create_key: MagicMock,
        _delete_value: MagicMock,
    ) -> None:
        StartupManager().set_enabled(False)
