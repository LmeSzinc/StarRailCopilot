import re

from module.base.timer import Timer
from module.logger import logger
from module.ocr.ocr import Ocr
from tasks.base.ui import UI
from tasks.login.assets.assets_login_uid import OCR_UID


class OcrUid(Ocr):
    def after_process(self, result):
        return result

    def format_result(self, result):
        result = result.replace('：', ':')
        if ':' in result:
            _, _, result = result.partition(':')
        if 'UID' in result:
            _, _, result = result.partition('UID')

        res = re.search(r'(\d+)', result)
        if res:
            result = int(res.group(1))
        else:
            logger.warning(f'No digit found in {result}')
            return 0

        if result < 100000000:
            logger.warning(f'UID too short: {result}')
            return 0
        if result > 10000000000:
            logger.warning(f'UID too long: {result}')
            return 0
        return result


class UIDHandler(UI):
    def get_uid(self, retry=True):
        """
        Get uid from current image

        Returns:
            int: or 0 if failed
        """
        ocr = OcrUid(OCR_UID)

        timeout = Timer(1.5, count=3).start()
        for _ in self.loop():
            result = ocr.ocr_single_line(self.device.image)
            if result:
                return result
            if not retry:
                return result
            if timeout.reached():
                logger.warning('Get UID timeout')
                break
