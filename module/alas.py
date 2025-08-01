import threading
import time
from datetime import datetime, timedelta

import inflection
from cached_property import cached_property

from module.base.decorator import del_cached_property
from module.config.config import AzurLaneConfig, TaskEnd
from module.config.deep import deep_get, deep_set
from module.exception import *
from module.logger import logger, save_error_log
from module.notify import handle_notify


class AzurLaneAutoScript:
    stop_event: threading.Event = None

    def __init__(self, config_name='alas'):
        logger.hr('Start', level=0)
        self.config_name = config_name
        # Skip first restart
        self.is_first_task = True
        # Failure count of tasks
        # Key: str, task name, value: int, failure count
        self.failure_record = {}

    @cached_property
    def config(self):
        try:
            config = AzurLaneConfig(config_name=self.config_name)
            return config
        except RequestHumanTakeover:
            logger.critical('Request human takeover')
            exit(1)
        except Exception as e:
            logger.exception(e)
            exit(1)

    @cached_property
    def device(self):
        try:
            from module.device.device import Device
            device = Device(config=self.config)
            return device
        except RequestHumanTakeover:
            logger.critical('Request human takeover')
            exit(1)
        except Exception as e:
            logger.exception(e)
            exit(1)

    @cached_property
    def checker(self):
        try:
            from module.server_checker import ServerChecker
            checker = ServerChecker(server=self.config.Emulator_PackageName)
            return checker
        except Exception as e:
            logger.exception(e)
            exit(1)

    def restart(self):
        raise NotImplemented

    def start(self):
        raise NotImplemented

    def stop(self):
        raise NotImplemented

    def goto_main(self):
        raise NotImplemented

    def run(self, command):
        try:
            self.device.screenshot()
            self.device.screenshot_tracking.clear()
            self.__getattribute__(command)()
            return True
        except TaskEnd:
            return True
        except GameNotRunningError as e:
            logger.warning(e)
            self.config.task_call('Restart')
            return False
        except (GameStuckError, GameTooManyClickError) as e:
            logger.error(e)
            self.save_error_log()
            logger.warning(f'Game stuck, {self.device.package} will be restarted in 10 seconds')
            logger.warning('If you are playing by hand, please stop Src')
            self.config.task_call('Restart')
            self.device.sleep(10)
            return False
        except GameBugError as e:
            logger.warning(e)
            self.save_error_log()
            logger.warning('An error has occurred in Star Rail game client, Src is unable to handle')
            logger.warning(f'Restarting {self.device.package} to fix it')
            self.config.task_call('Restart')
            self.device.sleep(10)
            return False
        except GamePageUnknownError:
            # logger.info('Game server may be under maintenance or network may be broken, check server status now')
            self.checker.check_now()
            if self.checker.is_available():
                logger.critical('Game page unknown')
                self.save_error_log()
                handle_notify(
                    self.config.Error_OnePushConfig,
                    title=f"Src <{self.config_name}> crashed",
                    content=f"<{self.config_name}> GamePageUnknownError",
                )
                exit(1)
            else:
                self.checker.wait_until_available()
                return False
        except HandledError as e:
            logger.error(e)
            return False
        except ScriptError as e:
            logger.exception(e)
            self.error_postprocess()
            logger.critical('This is likely to be a mistake of developers, but sometimes just random issues')
            self.save_error_log()
            handle_notify(
                self.config.Error_OnePushConfig,
                title=f"Src <{self.config_name}> crashed",
                content=f"<{self.config_name}> ScriptError",
            )
            exit(1)
        except RequestHumanTakeover:
            logger.critical('Request human takeover')
            self.error_postprocess()
            handle_notify(
                self.config.Error_OnePushConfig,
                title=f"Src <{self.config_name}> crashed",
                content=f"<{self.config_name}> RequestHumanTakeover",
            )
            exit(1)
        except Exception as e:
            logger.exception(e)
            self.error_postprocess()
            self.save_error_log()
            handle_notify(
                self.config.Error_OnePushConfig,
                title=f"Src <{self.config_name}> crashed",
                content=f"<{self.config_name}> Exception occured",
            )
            exit(1)

    def save_error_log(self):
        """
        Save last 60 screenshots in ./log/error/<timestamp>
        Save logs to ./log/error/<timestamp>/log.txt
        """
        save_error_log(config=self.config, device=self.device)

    def error_postprocess(self):
        """
        Do something when error occurred
        """
        pass

    def wait_until(self, future):
        """
        Wait until a specific time.

        Args:
            future (datetime):

        Returns:
            bool: True if wait finished, False if config changed.
        """
        future = future + timedelta(seconds=1)
        self.config.start_watching()
        while 1:
            if datetime.now() > future:
                return True
            if self.stop_event is not None:
                if self.stop_event.is_set():
                    logger.info("Update event detected")
                    logger.info(f"[{self.config_name}] exited. Reason: Update")
                    exit(0)

            time.sleep(5)

            if self.config.should_reload():
                return False

    def get_next_task(self):
        """
        Returns:
            str: Name of the next task.
        """
        while 1:
            task = self.config.get_next()
            self.config.task = task
            self.config.bind(task)

            from module.base.resource import release_resources
            if self.config.task.command != 'Alas':
                release_resources(next_task=task.command)

            if task.next_run > datetime.now():
                logger.info(f'Wait until {task.next_run} for task `{task.command}`')
                self.is_first_task = False
                method = self.config.Optimization_WhenTaskQueueEmpty
                if method == 'close_game':
                    logger.info('Close game during wait')
                    self.run('stop')
                    release_resources()
                    self.device.release_during_wait()
                    if not self.wait_until(task.next_run):
                        del_cached_property(self, 'config')
                        continue
                    if task.command != 'Restart':
                        self.config.task_call('Restart')
                        del_cached_property(self, 'config')
                        continue
                elif method == 'goto_main':
                    logger.info('Goto main page during wait')
                    self.run('goto_main')
                    release_resources()
                    self.device.release_during_wait()
                    if not self.wait_until(task.next_run):
                        del_cached_property(self, 'config')
                        continue
                elif method == 'stay_there':
                    logger.info('Stay there during wait')
                    release_resources()
                    self.device.release_during_wait()
                    if not self.wait_until(task.next_run):
                        del_cached_property(self, 'config')
                        continue
                elif method == 'close_emulator':
                    logger.info('Close emulator during wait')
                    self.run('stop')
                    release_resources()
                    self.device.release_during_wait()
                    # 关闭模拟器
                    try:
                        self.device.emulator_stop()
                        logger.info('Emulator stopped successfully')
                    except Exception as e:
                        logger.warning(f'Failed to stop emulator: {e}')
                    if not self.wait_until(task.next_run):
                        del_cached_property(self, 'config')
                        del_cached_property(self, 'device')
                        continue
                    # 重新启动模拟器
                    if task.command != 'Restart':
                        self.config.task_call('Restart')
                        del_cached_property(self, 'config')
                        del_cached_property(self, 'device')
                        continue
                else:
                    logger.warning(f'Invalid Optimization_WhenTaskQueueEmpty: {method}, fallback to stay_there')
                    release_resources()
                    self.device.release_during_wait()
                    if not self.wait_until(task.next_run):
                        del_cached_property(self, 'config')
                        continue
            break

        AzurLaneConfig.is_hoarding_task = False
        return task.command

    def loop(self):
        logger.set_file_logger(self.config_name)
        logger.info(f'Start scheduler loop: {self.config_name}')

        while 1:
            # Check update event from GUI
            if self.stop_event is not None:
                if self.stop_event.is_set():
                    logger.info("Update event detected")
                    logger.info(f"[{self.config_name}] exited.")
                    break
            # Check game server maintenance
            self.checker.wait_until_available()
            if self.checker.is_recovered():
                # There is an accidental bug hard to reproduce
                # Sometimes, config won't be updated due to blocking
                # even though it has been changed
                # So update it once recovered
                del_cached_property(self, 'config')
                logger.info('Server or network is recovered. Restart game client')
                self.config.task_call('Restart')
            # Get task
            task = self.get_next_task()
            # Init device and change server
            _ = self.device
            self.device.config = self.config
            # Skip first restart
            if self.is_first_task and task == 'Restart':
                logger.info('Skip task `Restart` at scheduler start')
                self.config.task_delay(server_update=True)
                del_cached_property(self, 'config')
                continue

            # Run
            logger.info(f'Scheduler: Start task `{task}`')
            self.device.stuck_record_clear()
            self.device.click_record_clear()
            logger.hr(task, level=0)
            success = self.run(inflection.underscore(task))
            logger.info(f'Scheduler: End task `{task}`')
            self.is_first_task = False

            # Check failures
            failed = deep_get(self.failure_record, keys=task, default=0)
            failed = 0 if success else failed + 1
            deep_set(self.failure_record, keys=task, value=failed)
            if failed >= 3:
                logger.critical(f"Task `{task}` failed 3 or more times.")
                logger.critical("Possible reason #1: You haven't used it correctly. "
                                "Please read the help text of the options.")
                logger.critical("Possible reason #2: There is a problem with this task. "
                                "Please contact developers or try to fix it yourself.")
                logger.critical('Request human takeover')
                handle_notify(
                    self.config.Error_OnePushConfig,
                    title=f"Src <{self.config_name}> crashed",
                    content=f"<{self.config_name}> RequestHumanTakeover\nTask `{task}` failed 3 or more times.",
                )
                exit(1)

            if success:
                del_cached_property(self, 'config')
                continue
            else:
                # self.config.task_delay(success=False)
                del_cached_property(self, 'config')
                self.checker.check_now()
                continue


if __name__ == '__main__':
    alas = AzurLaneAutoScript()
    alas.loop()
