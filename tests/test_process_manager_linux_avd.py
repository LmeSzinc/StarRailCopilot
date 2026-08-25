import unittest
from unittest.mock import patch

from module.webui.process_manager import ProcessManager


class ProcessManagerExceptionBoundaryTest(unittest.TestCase):
    def test_stop_grace_does_not_swallow_control_flow_exceptions(self):
        """Catches ordinary config fallback swallowing process control flow."""
        manager = object.__new__(ProcessManager)
        manager.config_name = 'test'

        for error in (SystemExit(2), KeyboardInterrupt()):
            with self.subTest(error=type(error).__name__), patch(
                'module.webui.process_manager.load_config',
                side_effect=error,
            ):
                with self.assertRaises(type(error)):
                    manager._linux_avd_stop_grace()


if __name__ == '__main__':
    unittest.main()
