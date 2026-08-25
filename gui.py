import threading
from multiprocessing import Event, Process

from module.device.env import IS_LINUX
from module.logger import logger
from module.webui.setting import State


def func(ev: threading.Event):
    import argparse
    import asyncio
    import sys

    import uvicorn

    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    State.restart_event = ev

    parser = argparse.ArgumentParser(description="Alas web service")
    parser.add_argument(
        "--host",
        type=str,
        help="Host to listen. Default to WebuiHost in deploy setting",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        help="Port to listen. Default to WebuiPort in deploy setting",
    )
    parser.add_argument(
        "-k", "--key", type=str, help="Password of alas. No password by default"
    )
    parser.add_argument(
        "--cdn",
        action="store_true",
        help="Use jsdelivr cdn for pywebio static files (css, js). Self host cdn by default.",
    )
    parser.add_argument(
        "--electron", action="store_true", help="Runs by electron client."
    )
    parser.add_argument(
        "--ssl-key", dest="ssl_key", type=str, help="SSL key file path for HTTPS support"
    )
    parser.add_argument(
        "--ssl-cert", type=str, help="SSL certificate file path for HTTPS support"
    )
    parser.add_argument(
        "--run",
        nargs="+",
        type=str,
        help="Run alas by config names on startup",
    )
    args, _ = parser.parse_known_args()

    host = args.host or State.deploy_config.WebuiHost or "0.0.0.0"
    port = args.port or int(State.deploy_config.WebuiPort) or 22367
    ssl_key = args.ssl_key or State.deploy_config.WebuiSSLKey
    ssl_cert = args.ssl_cert or State.deploy_config.WebuiSSLCert
    ssl = ssl_key is not None and ssl_cert is not None
    State.electron = args.electron

    logger.hr("Launcher config")
    logger.attr("Host", host)
    logger.attr("Port", port)
    logger.attr("SSL", ssl)
    logger.attr("Electron", args.electron)
    logger.attr("Reload", ev is not None)

    if State.electron:
        # https://github.com/LmeSzinc/AzurLaneAutoScript/issues/2051
        logger.info("Electron detected, remove log output to stdout")
        from module.logger.logger import console_hdlr
        logger.removeHandler(console_hdlr)

    if ssl_cert is None and ssl_key is not None:
        logger.error("SSL key provided without certificate. Please provide both SSL key and certificate.")
    elif ssl_key is None and ssl_cert is not None:
        logger.error("SSL certificate provided without key. Please provide both SSL key and certificate.")

    if ssl:
        uvicorn.run("module.webui.app:app", host=host, port=port, factory=True, ssl_keyfile=ssl_key, ssl_certfile=ssl_cert)
    else:
        uvicorn.run("module.webui.app:app", host=host, port=port, factory=True)


def supervise_web_process(
        process_factory=None,
        event_factory=Event,
        wait_interval=1,
):
    """Keep the Linux Web child alive after an unexpected worker exit.

    Args:
        process_factory: Optional callable creating a child process.
        event_factory: Optional callable creating the reload event.
        wait_interval (float): Seconds between child state checks.
    """
    if process_factory is None:
        process_factory = lambda event: Process(target=func, args=(event,))

    should_exit = False
    while not should_exit:
        event = event_factory()
        process = process_factory(event)
        process.start()
        while not should_exit:
            try:
                reload_requested = event.wait(wait_interval)
            except KeyboardInterrupt:
                should_exit = True
                if IS_LINUX:
                    _stop_web_process(process)
                break
            if reload_requested:
                process.kill()
                break
            if process.is_alive():
                continue
            if not IS_LINUX:
                should_exit = True
                break
            logger.warning(
                f'Web server process exited unexpectedly with code '
                f'{getattr(process, "exitcode", None)}; restarting'
            )
            break
        if not should_exit:
            process.join()


def _stop_web_process(process, grace=None):
    """Stop a Web child without leaving it behind on parent shutdown.

    Args:
        process: Multiprocessing child process to terminate.
        grace (float): Seconds to wait for graceful cleanup before killing it.
    """
    if grace is None:
        grace = 90 if IS_LINUX else 5
    try:
        process.terminate()
    except (OSError, RuntimeError):
        pass
    try:
        process.join(timeout=grace)
    except (OSError, RuntimeError):
        pass
    if process.is_alive():
        try:
            process.kill()
        except (OSError, RuntimeError):
            pass
        try:
            process.join(timeout=5)
        except (OSError, RuntimeError):
            pass


if __name__ == "__main__":
    if State.deploy_config.EnableReload:
        supervise_web_process()
    else:
        func(None)
