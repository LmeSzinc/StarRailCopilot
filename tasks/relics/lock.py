from module.base.timer import Timer
from module.exception import ScriptError
from module.logger import logger
from tasks.base.ui import UI
from tasks.relics.assets.assets_relics_lock import *


class RelicState:
    locked = 'locked'
    discarded = 'discarded'
    free = 'free'
    unknown = 'unknown'


class RelicLock(UI):
    def get_relic_state(self, sim=0.7) -> str:
        if LOCKED.match_template_luma(self.device.image, similarity=sim):
            state = RelicState.locked
            logger.attr('RelicState', state)
            return state
        if DISCARDED.match_template_luma(self.device.image, similarity=sim):
            state = RelicState.discarded
            logger.attr('RelicState', state)
            return state
        if LOCK_CLICK.match_template_luma(self.device.image, similarity=sim) \
                and DISCARD_CLICK.match_template_luma(self.device.image, similarity=sim):
            state = RelicState.free
            logger.attr('RelicState', state)
            return state
        state = RelicState.unknown
        logger.attr('RelicState', state)
        return state

    def relic_lock(self, skip_first_screenshot=True):
        click_interval = Timer(1.5, count=3)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            state = self.get_relic_state()
            if state == RelicState.locked:
                break
            if state == RelicState.discarded:
                if click_interval.reached():
                    self.device.click(DISCARDED)
                    click_interval.reset()
            if state == RelicState.free:
                if click_interval.reached():
                    self.device.click(LOCK_CLICK)
                    click_interval.reset()

    def relic_discard(self, skip_first_screenshot=True):
        click_interval = Timer(1.5, count=3)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            state = self.get_relic_state()
            if state == RelicState.discarded:
                break
            if state == RelicState.locked:
                if click_interval.reached():
                    self.device.click(LOCKED)
                    click_interval.reset()
            if state == RelicState.free:
                if click_interval.reached():
                    self.device.click(DISCARD_CLICK)
                    click_interval.reset()

    def relic_free(self, skip_first_screenshot=True):
        click_interval = Timer(1.5, count=3)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            state = self.get_relic_state()
            if state == RelicState.free:
                break
            if state == RelicState.locked:
                if click_interval.reached():
                    self.device.click(LOCKED)
                    click_interval.reset()
            if state == RelicState.discarded:
                if click_interval.reached():
                    self.device.click(DISCARDED)
                    click_interval.reset()

    def relic_wait_state(self, skip_first_screenshot=True):
        """
        Wait first relic state
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            state = self.get_relic_state()
            if state != RelicState.unknown:
                return state

    def relic_reset_state(self, skip_first_screenshot=True):
        """
        Double click lock to reset relic list
        """
        logger.hr('Relic reset list')
        state = self.relic_wait_state(skip_first_screenshot)
        if state == RelicState.free:
            self.relic_lock()
            self.relic_free()
        elif state == RelicState.locked:
            self.relic_free()
            self.relic_lock()
        elif state == RelicState.discarded:
            self.relic_free()
            self.relic_discard()
        else:
            raise ScriptError(f'Unknown relic state: {state}')
