import os
import time
from typing import Iterable

from deploy.Windows.config import DeployConfig
from deploy.Windows.logger import Progress, logger
from deploy.Windows.utils import cached_property, iter_process


class AlasManager(DeployConfig):
    @cached_property
    def alas_folder(self):
        return [
            self.filepath(self.PythonExecutable),
            self.root_filepath
        ]

    @cached_property
    def self_pid(self):
        return os.getpid()

    def list_process(self) -> "list[tuple[int, list[str]]]":
        logger.info('List process')
        process_data = list(iter_process())
        logger.info(f'Found {len(process_data)} processes')
        return process_data

    def iter_process_by_names(self, names, in_alas=False) -> "Iterable[int]":
        """
        Args:
            names (str, list[str]): process name, such as 'alas.exe'
            in_alas (bool): If the output process must in Alas

        Yields:
            pid:
        """
        if not isinstance(names, list):
            names = [names]
        try:
            for pid, cmdline in self.list_process():
                if pid == self.self_pid:
                    continue
                exe = cmdline[0]
                name = os.path.basename(exe)
                if not (name and name in names):
                    continue

                if in_alas:
                    exe = exe.replace(r"\\", "/").replace("\\", "/")
                    for folder in self.alas_folder:
                        if folder in exe:
                            yield pid
                else:
                    yield pid
        except Exception as e:
            logger.info(str(e))
            return False

    def kill_process(self, pid: int):
        self.execute(f'taskkill /f /t /pid {pid}', allow_failure=True, output=False)

    def alas_kill(self):
        for _ in range(10):
            logger.hr(f'Kill existing Alas', 0)
            proc_list = list(self.iter_process_by_names(['python.exe'], in_alas=True))
            if not len(proc_list):
                Progress.KillExisting()
                return True
            for proc in proc_list:
                logger.info(proc)
                self.kill_process(proc)

        logger.warning('Unable to kill existing Alas, skip')
        Progress.KillExisting()
        return False


if __name__ == '__main__':
    self = AlasManager()
    start = time.time()
    self.alas_kill()
    print(time.time() - start)
