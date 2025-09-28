from datetime import timedelta

from module.base.utils import crop
from module.config.stored.classes import now
from module.config.utils import DEFAULT_TIME, get_server_next_monday_update, get_server_next_update
from module.logger import logger
from module.ocr.ocr import DigitCounter
from tasks.base.ui import UI
from tasks.dungeon.assets.assets_dungeon_state import OCR_SIMUNI_POINT, OCR_SIMUNI_POINT_OFFSET
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
        value, _, total = ocr.ocr_single_line(crop(image, area, copy=False), direct_ocr=True)
        if total and value <= total:
            logger.attr('SimulatedUniverse', f'{value}/{total}')
            self.config.stored.SimulatedUniverse.set(value, total)
            return value
        else:
            logger.warning(f'Invalid SimulatedUniverse points: {value}/{total}')
            return 0

    # def dungeon_update_simuni(self):
    #     """
    #     Update rogue weekly points, stamina, immersifier
    #     Run in a new thread to be faster as data is not used immediately
    #
    #     Page:
    #         in: page_guide, Survival_Index, Simulated_Universe
    #     """
    #     logger.info('dungeon_update_simuni')
    #
    #     def func(image):
    #         logger.info('Update thread start')
    #         with self.config.multi_set():
    #             # self.dungeon_get_simuni_point(image)
    #             self.update_stamina_status(image)
    #
    #     ModuleBase.worker.submit(func, self.device.image)

    def dungeon_stamina_delay(self, dungeon: DungeonList):
        """
        Delay tasks that use stamina
        """
        limit = 120

        # Double event is not yet finished, do it today as possible
        update = get_server_next_update(self.config.Scheduler_ServerUpdate)
        diff = update - now()
        run_double = False
        if self.config.stored.DungeonDouble.relic > 0:
            if diff < timedelta(hours=4):
                # 4h recover 40 stamina, run double relic at today
                logger.info(f'Just less than 4h til the next day, '
                            f'double relic event is not yet finished, wait until 40')
                run_double = True
                limit = 40
        if self.config.stored.DungeonDouble.calyx > 0:
            if diff < timedelta(hours=3):
                logger.info(f'Just less than 3h til the next day, '
                            f'double calyx event is not yet finished, wait until 10')
                run_double = True
                limit = 10
            elif diff < timedelta(hours=6):
                logger.info(f'Just less than 6h til the next day, '
                            f'double calyx event is not yet finished, wait until 30')
                run_double = True
                limit = 30

        # Recover 1 trailbaze power each 6 minutes
        current = self.config.stored.TrailblazePower.value
        cover = max(limit - current, 0) * 6
        future = now() + timedelta(minutes=cover)
        logger.info(f'Currently has {current} need {cover} minutes to reach {limit}')

        # Align server update
        if not run_double and update - future < timedelta(hours=2):
            logger.info('Approaching next day, delay to server update instead')
            future = update

        # Save stamina for the next week
        next_monday = get_server_next_monday_update('04:00')
        if next_monday - future < timedelta(hours=4):
            logger.info(f'Approaching next monday, delay to {next_monday} instead')
            future = next_monday

        tasks = ['Dungeon', 'Weekly', 'Ornament']
        with self.config.multi_set():
            for task in tasks:
                next_run = self.config.cross_get(keys=f'{task}.Scheduler.NextRun', default=DEFAULT_TIME)
                if future > next_run:
                    logger.info(f"Delay task `{task}` to {future}")
                    self.config.cross_set(keys=f'{task}.Scheduler.NextRun', value=future)
