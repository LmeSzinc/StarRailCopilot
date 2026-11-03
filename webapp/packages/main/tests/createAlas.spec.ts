import {expect, test, vi} from 'vitest';
import {handleAlasEnd} from '../src/serviceLogic/createAlas';

test('does not throw when the backend process ends with shutdown output', () => {
  const context = {
    sendLaunchLog: vi.fn(),
  };
  const shutdownOutput = 'INFO: Uvicorn running on http://127.0.0.1:22370';

  expect(() => handleAlasEnd(context, shutdownOutput)).not.toThrow();
  expect(context.sendLaunchLog).toHaveBeenCalledWith(shutdownOutput);
});
