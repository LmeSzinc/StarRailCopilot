import unittest
from unittest.mock import patch

import gui


class WebProcessSupervisorTest(unittest.TestCase):
    def test_unexpected_server_exit_starts_replacement(self):
        """Catches a clean Uvicorn child exit taking down the persistent Web service."""
        supervisor = getattr(gui, 'supervise_web_process', None)
        self.assertIsNotNone(supervisor, 'gui.py must expose the Web process supervisor')

        started = []
        joined = []
        events_created = 0

        class Event:
            def __init__(self, stop_supervisor):
                self.stop_supervisor = stop_supervisor

            def wait(self, timeout):
                if self.stop_supervisor:
                    raise KeyboardInterrupt
                return False

        class Process:
            def __init__(self, number):
                self.number = number
                self.running = False

            def start(self):
                self.running = False
                started.append(self.number)

            def is_alive(self):
                return self.running

            def terminate(self):
                self.running = False

            def kill(self):
                self.running = False

            def join(self, timeout=None):
                joined.append(self.number)

        def event_factory():
            nonlocal events_created
            events_created += 1
            return Event(stop_supervisor=events_created == 2)

        def process_factory(event):
            return Process(events_created)

        supervisor(
            process_factory=process_factory,
            event_factory=event_factory,
            wait_interval=0,
        )

        self.assertEqual(started, [1, 2])
        self.assertEqual(joined, [1, 2])

    def test_non_linux_unexpected_exit_keeps_upstream_supervisor_behavior(self):
        """Catches Linux Web restart behavior leaking into other platforms."""
        started = []

        class Event:
            def wait(self, timeout):
                return False

        class Process:
            def start(self):
                started.append(True)

            def is_alive(self):
                return False

            def join(self, timeout=None):
                raise AssertionError('upstream does not join this exit path')

        with patch('gui.IS_LINUX', False):
            gui.supervise_web_process(
                process_factory=lambda event: Process(),
                event_factory=Event,
                wait_interval=0,
            )

        self.assertEqual(started, [True])

    def test_keyboard_interrupt_stops_the_child_before_supervisor_exit(self):
        """Catches Ctrl-C leaving Uvicorn running after the parent exits."""
        class Event:
            def wait(self, timeout):
                raise KeyboardInterrupt

        class Process:
            def __init__(self):
                self.terminate_calls = 0
                self.kill_calls = 0
                self.join_calls = []
                self.running = True

            def start(self):
                pass

            def is_alive(self):
                return self.running

            def terminate(self):
                self.terminate_calls += 1

            def kill(self):
                self.kill_calls += 1
                self.running = False

            def join(self, timeout=None):
                self.join_calls.append(timeout)

        process = Process()
        gui.supervise_web_process(
            process_factory=lambda event: process,
            event_factory=Event,
            wait_interval=0,
        )

        self.assertEqual(process.terminate_calls, 1)
        self.assertEqual(process.kill_calls, 1)
        self.assertEqual(process.join_calls, [90, 5])

    def test_non_linux_keyboard_interrupt_keeps_upstream_child_handling(self):
        """Catches Linux Ctrl-C process handling changing Windows or macOS."""
        class Event:
            def wait(self, timeout):
                raise KeyboardInterrupt

        class Process:
            def start(self):
                pass

            def terminate(self):
                raise AssertionError('non-Linux supervisor must not terminate the child')

            def join(self, timeout=None):
                raise AssertionError('upstream does not join this exit path')

        with patch('gui.IS_LINUX', False):
            gui.supervise_web_process(
                process_factory=lambda event: Process(),
                event_factory=Event,
                wait_interval=0,
            )


if __name__ == '__main__':
    unittest.main()
