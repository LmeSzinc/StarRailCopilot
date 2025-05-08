import os
from typing import Callable, Generic, Iterable, TypeVar

T = TypeVar("T")


class cached_property(Generic[T]):
    """
    cached-property from https://github.com/pydanny/cached-property
    Add typing support

    A property that is only computed once per instance and then replaces itself
    with an ordinary attribute. Deleting the attribute resets the property.
    Source: https://github.com/bottlepy/bottle/commit/fa7733e075da0d790d809aa3d2f53071897e6f76
    """

    def __init__(self, func: Callable[..., T]):
        self.func = func

    def __get__(self, obj, cls) -> T:
        if obj is None:
            return self

        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


def iter_folder(folder, is_dir=False, ext=None):
    """
    Args:
        folder (str):
        is_dir (bool): True to iter directories only
        ext (str): File extension, such as `.yaml`

    Yields:
        str: Absolute path of files
    """
    try:
        files = os.listdir(folder)
    except FileNotFoundError:
        return

    for file in files:
        sub = os.path.join(folder, file)
        if is_dir:
            if os.path.isdir(sub):
                yield sub.replace('\\\\', '/').replace('\\', '/')
        elif ext is not None:
            if not os.path.isdir(sub):
                _, extension = os.path.splitext(file)
                if extension == ext:
                    yield os.path.join(folder, file).replace('\\\\', '/').replace('\\', '/')
        else:
            yield os.path.join(folder, file).replace('\\\\', '/').replace('\\', '/')


def iter_process() -> "Iterable[tuple[int, list[str]]]":
    """
    Yields:
        int: pid
        list[str]: cmdline, and it's guaranteed to have at least one element
    """
    try:
        import psutil
    except ModuleNotFoundError:
        return

    if psutil.WINDOWS:
        # Since this is a one-time-usage, we access psutil._psplatform.Process directly
        # to bypass the call of psutil.Process.is_running().
        # This only costs about 0.017s.
        # If you do psutil.process_iter(['pid', 'cmdline']) it will take over 1s
        import psutil._psutil_windows as cetx
        for pid in psutil.pids():
            # 0 and 4 are always represented in taskmgr and process-hacker
            if pid == 0 or pid == 4:
                continue
            try:
                # This would be fast on psutil<=5.9.8 taking overall time 0.027s
                # but taking 0.39s on psutil>=6.0.0
                cmdline = cetx.proc_cmdline(pid, use_peb=True)
            except (psutil.AccessDenied, psutil.NoSuchProcess, IndexError, OSError):
                # psutil.AccessDenied
                # NoSuchProcess: process no longer exists (pid=xxx)
                # ProcessLookupError: [Errno 3] assume no such process (originated from psutil_pid_is_running -> 0)
                # OSError: [WinError 87] 参数错误。: '(originated from ReadProcessMemory)'
                continue

            # Validate cmdline
            if not cmdline:
                continue
            try:
                exe = cmdline[0]
            except IndexError:
                continue
            # \??\C:\Windows\system32\conhost.exe
            if exe.startswith(r'\??'):
                continue
            yield pid, cmdline
    else:
        # No optimizations yet
        for pid in psutil.pids():
            proc = psutil._psplatform.Process(pid)
            try:
                cmdline = proc.cmdline()
            except (psutil.AccessDenied, psutil.NoSuchProcess, IndexError, OSError):
                continue

            # Validate cmdline
            if not cmdline:
                continue
            try:
                cmdline[0]
            except IndexError:
                continue
            yield pid, cmdline
