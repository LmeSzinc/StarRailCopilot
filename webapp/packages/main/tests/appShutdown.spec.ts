import {beforeEach, expect, test, vi} from 'vitest';
import {ShutdownCoordinator} from '../src/appShutdown';

beforeEach(() => {
  vi.clearAllMocks();
});

test('waits for the Python process tree to stop before quitting Electron', async () => {
  let finishBackendShutdown: (() => void) | undefined;
  const stopBackend = vi.fn(
    () =>
      new Promise<void>(resolve => {
        finishBackendShutdown = resolve;
      }),
  );
  const quitElectron = vi.fn();
  const shutdown = new ShutdownCoordinator(stopBackend, quitElectron);

  const completed = shutdown.request();

  expect(stopBackend).toHaveBeenCalledOnce();
  expect(quitElectron).not.toHaveBeenCalled();
  expect(shutdown.readyToQuit).toBe(false);

  finishBackendShutdown?.();
  await completed;

  expect(quitElectron).toHaveBeenCalledOnce();
  expect(shutdown.readyToQuit).toBe(true);
});

test('coalesces concurrent shutdown requests', async () => {
  const stopBackend = vi.fn(() => Promise.resolve());
  const quitElectron = vi.fn();
  const shutdown = new ShutdownCoordinator(stopBackend, quitElectron);

  await Promise.all([shutdown.request(), shutdown.request()]);

  expect(stopBackend).toHaveBeenCalledOnce();
  expect(quitElectron).toHaveBeenCalledOnce();
});

test('still quits Electron if the backend process is already gone', async () => {
  const error = new Error('process not found');
  const stopBackend = vi.fn(() => Promise.reject(error));
  const quitElectron = vi.fn();
  const reportError = vi.fn();
  const shutdown = new ShutdownCoordinator(stopBackend, quitElectron, reportError);

  await shutdown.request();

  expect(reportError).toHaveBeenCalledWith(error);
  expect(quitElectron).toHaveBeenCalledOnce();
  expect(shutdown.readyToQuit).toBe(true);
});
