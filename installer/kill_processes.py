import sys
import psutil
import os

home = sys.argv[1]
current_pid = os.getpid()

targets = [
    home + r'\src.exe',
    home + r'\toolkit\python.exe',
    home + r'\toolkit\Lib\site-packages\adbutils\binaries\adb.exe',
]

for exe_path in targets:
    for proc in psutil.process_iter(['exe', 'pid']):
        # Don't kill itself
        if proc.info['exe'] and proc.info['exe'].lower() == exe_path.lower():
            if proc.info['pid'] != current_pid:
                try:
                    proc.kill()
                except:
                    pass