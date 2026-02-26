from module.logger import logger
from tasks.assignment.assets.assets_assignment_state import *
from tasks.base.page import page_assignment
from tasks.base.ui import UI


class Assignment(UI):
    def _get_state(self):
        for state in [
            STATE_EMPTY,
            STATE_REWARD,
            STATE_WORKING,
        ]:
            if self.appear(state):
                return state
        return None

    def ensure_assignment(self):
        logger.hr('Ensure assignment', level=1)
        for _ in self.loop():
            if self.handle_tutorial():
                continue
            if self.appear_then_click(TUTORIAL_ADD):
                continue
            if self.appear_then_click(TUTORIAL_SELECT):
                continue
            # end
            state = self._get_state()
            if state is not None:
                logger.attr('AssignmentState', state)
                return state

        return None

    def assignment_claim(self):
        logger.hr('Assignment claim', level=1)
        # STATE_REWARD -> reward popup
        for _ in self.loop():
            if self.handle_reward():
                break
            if self.appear_then_click(STATE_REWARD):
                continue
            if self.appear(STATE_WORKING):
                logger.info(f'Early ended at {STATE_WORKING}')
                return
            if self.appear(STATE_EMPTY):
                logger.info(f'Early ended at {STATE_EMPTY}')
                return

        # reward popup -> STATE_WORKING
        for _ in self.loop():
            if self.handle_reward():
                break
            state = self._get_state()
            if state is not None:
                logger.attr('AssignmentState', state)
                return state

    def run(self):
        self.ui_ensure(page_assignment)
        state = self.ensure_assignment()
        if state == STATE_REWARD:
            self.assignment_claim()
        elif state == STATE_WORKING:
            logger.info('No assignment reward to claim')
        elif state == STATE_EMPTY:
            logger.warning('Assignment not selected, please select them manually')
        else:
            logger.warning(f'Unknown assignment state {state}')

        # scheduler
        self.config.task_delay(server_update=True)
