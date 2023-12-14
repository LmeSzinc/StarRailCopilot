from datetime import timedelta

from module.base.base import ModuleBase
from module.base.timer import Timer
from module.base.utils import crop
from module.config.stored.classes import now
from module.config.utils import DEFAULT_TIME
from module.logger import logger
from module.ocr.ocr import DigitCounter
from tasks.base.ui import UI
from tasks.dungeon.assets.assets_dungeon_state import OCR_SIMUNI_POINT, OCR_SIMUNI_POINT_OFFSET, OCR_STAMINA
from tasks.dungeon.keywords import DungeonList


class OcrSimUniPoint(DigitCounter):
    def after_process(self, result):
        result = super().after_process(result)
        result = result.replace('O', '0').replace('o', '0')
        return result


class DungeonState(UI):
    def dungeon_get_simuni_point(self, image=None) -> int:
        """
        Page:
            in: page_guide, Survival_Index, Simulated_Universe
        """
        logger.info('Get simulated universe points')
        if image is None:
            image = self.device.image

        _ = OCR_SIMUNI_POINT_OFFSET.match_template(image)
        OCR_SIMUNI_POINT.load_offset(OCR_SIMUNI_POINT_OFFSET)
        area = (
            OCR_SIMUNI_POINT.area[0],
            OCR_SIMUNI_POINT.button[1],
            OCR_SIMUNI_POINT.area[2],
            OCR_SIMUNI_POINT.button[3],
        )

        ocr = OcrSimUniPoint(OCR_SIMUNI_POINT)
        value, _, total = ocr.ocr_single_line(crop(image, area), direct_ocr=True)
        if total and value <= total:
            logger.attr('SimulatedUniverse', f'{value}/{total}')
            self.config.stored.SimulatedUniverse.set(value, total)
            return value
        else:
            logger.warning(f'Invalid SimulatedUniverse points: {value}/{total}')
            return 0

    def dungeon_update_stamina(self, image=None, skip_first_screenshot=True):
        """
        Returns:
            bool: If success

        Pages:
            in: page_guild, Survival_Index, Simulated_Universe
                or page_rogue, LEVEL_CONFIRM
                or rogue, REWARD_CLOSE
        """
        ocr = DigitCounter(OCR_STAMINA)
        timeout = Timer(1, count=2).start()
        if image is None:
            image = self.device.image
            use_cached_image = False
        else:
            skip_first_screenshot = True
            use_cached_image = True

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
                image = self.device.image

            stamina = (0, 0, 0)
            immersifier = (0, 0, 0)

            if timeout.reached():
                logger.warning('dungeon_update_stamina() timeout')
                return False

            for row in ocr.detect_and_ocr(image):
                if row.ocr_text.isdigit():
                    continue
                if row.ocr_text == '+':
                    continue
                if '/' not in row.ocr_text:
                    continue
                data = ocr.format_result(row.ocr_text)
                if data[2] == self.config.stored.TrailblazePower.FIXED_TOTAL:
                    stamina = data
                if data[2] == self.config.stored.Immersifier.FIXED_TOTAL:
                    immersifier = data

            if stamina[2] > 0 and immersifier[2] > 0:
                break
            if use_cached_image:
                logger.info('dungeon_update_stamina() ended')
                return

        stamina = stamina[0]
        immersifier = immersifier[0]
        logger.attr('TrailblazePower', stamina)
        logger.attr('Imersifier', immersifier)
        with self.config.multi_set():
            self.config.stored.TrailblazePower.value = stamina
            self.config.stored.Immersifier.value = immersifier
        return True

    def dungeon_update_simuni(self):
        """
        Update rogue weekly points, stamina, immersifier
        Run in a new thread to be faster as data is not used immediately

        Page:
            in: page_guide, Survival_Index, Simulated_Universe
        """
        logger.info('dungeon_update_simuni')

        def func(image):
            logger.info('Update thread start')
            with self.config.multi_set():
                self.dungeon_get_simuni_point(image)
                self.dungeon_update_stamina(image)

        ModuleBase.worker.submit(func, self.device.image)

    def dungeon_stamina_delay(self, dungeon: DungeonList):
        """
        Delay tasks that use stamina
        """
        if dungeon.is_Simulated_Universe:
            limit = 80
        elif dungeon.is_Cavern_of_Corrosion:
            limit = 80
        elif dungeon.is_Echo_of_War:
            limit = 30
        else:
            limit = 60
        # Recover 1 trailbaze power each 6 minutes
        current = self.config.stored.TrailblazePower.value
        cover = max(limit - current, 0) * 6
        future = now() + timedelta(minutes=cover)
        logger.info(f'Currently has {current} need {cover} minutes to reach {limit}')

        tasks = ['Dungeon', 'Weekly']
        with self.config.multi_set():
            for task in tasks:
                next_run = self.config.cross_get(keys=f'{task}.Scheduler.NextRun', default=DEFAULT_TIME)
                if future > next_run:
                    logger.info(f"Delay task `{task}` to {future}")
                    self.config.cross_set(keys=f'{task}.Scheduler.NextRun', value=future)
