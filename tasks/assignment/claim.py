from datetime import timedelta

from module.config.stored.classes import now
from module.logger import logger
from module.ocr.ocr import Duration
from tasks.assignment.assets.assets_assignment_claim import *
from tasks.assignment.assets.assets_assignment_ui import EVENT_COMPLETED
from tasks.assignment.dispatch import AssignmentDispatch
from tasks.assignment.keywords import AssignmentEntry, KEYWORDS_ASSIGNMENT_GROUP
from tasks.assignment.ui import ASSIGNMENT_ENTRY_LIST
from tasks.base.page import page_assignment


class AssignmentClaim(AssignmentDispatch):
    def claim(self, assignment: AssignmentEntry, duration_expected: int, should_redispatch: bool):
        """
        Args:
            assignment (AssignmentEntry):
            duration_expected (int): user specified duration
            should_redispatch (bool):

        Pages:
            in: CLAIM
            out: DISPATCHED or EMPTY_SLOT
        """
        redispatched = False
        self._claim_one()
        if should_redispatch:
            redispatched = self._is_duration_expected(duration_expected)
        self._exit_report(redispatched)
        if redispatched:
            self._wait_until_assignment_started()
            future = now() + timedelta(hours=duration_expected)
            logger.info(f'Assignment redispatched, will finish at {future}')
            self.dispatched[assignment] = future
            self.has_new_dispatch = True
        elif should_redispatch:
            # Re-select duration and dispatch
            self.goto_entry(assignment)
            self.dispatch(assignment, duration_expected)

    def _claim_one(self, skip_first_screenshot=True):
        """
        Pages:
            in: CLAIM
            out: REPORT
        """
        logger.info('Assignment claim one')
        self.interval_clear(CLAIM, interval=2)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            # End
            # Neither CLOSE_REPORT nor REDISPATCH is shown
            # If it is an EVENT assignment
            if self.appear(REPORT):
                logger.info('Assignment report appears')
                break
            # Claim rewards
            if self.appear_then_click(CLAIM, interval=2):
                continue

    def _claim_all(self, skip_first_screenshot=True):
        """
        Pages:
            in: CLAIM_ALL
            out: REPORT
        """
        logger.info('Assignment claim all')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            # End
            # Neither CLOSE_REPORT nor REDISPATCH is shown
            # If it is an EVENT assignment
            if self.appear(REPORT):
                logger.info('Assignment report appears')
                break
            # Claim rewards
            if self.appear_then_click(CLAIM_ALL, interval=2):
                continue

    def claim_all(self):
        """
        Do claim all if CLAIM_ALL appears
        """
        logger.hr('Assignment claim all', level=1)
        self.goto_group(KEYWORDS_ASSIGNMENT_GROUP.Character_Materials)
        if self.appear(CLAIM_ALL):
            self._claim_all()
            self._exit_report(should_redispatch=True)
            self._wait_until_assignment_started()
            self.has_new_dispatch = True
            # Load rows again to update remains
            ASSIGNMENT_ENTRY_LIST.load_rows(main=self)
            self._scan_ongoing()
            return True
        else:
            logger.info('No CLAIM_ALL button')
            self._scan_ongoing()
            return False

    def _exit_report(self, should_redispatch: bool):
        """
        Args:
            should_redispatch (bool): determined by user config and duration in report

        Pages:
            in: REPORT
            out: page_assignment
        """
        click_button = REDISPATCH if should_redispatch else CLOSE_REPORT
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            # End
            if self.appear(page_assignment.check_button):
                logger.info('Assignment report is closed')
                break
            if self.appear(EVENT_COMPLETED):
                logger.info('Event completed')
                return
            # Close report
            if self.appear(REPORT, interval=1):
                self.device.click(click_button)
                continue
        # Ensure report totally disappears
        self._wait_until_entry_loaded()

    def _is_duration_expected(self, duration: int) -> bool:
        """
        Check whether duration in assignment report page
        is the same as user specified

        Args:
            duration (int): user specified duration

        Returns:
            bool: If same.
        """
        duration_reported: timedelta = Duration(
            OCR_ASSIGNMENT_REPORT_TIME).ocr_single_line(self.device.image)
        return duration_reported.total_seconds() == duration * 3600

    def _scan_ongoing(self):
        logger.hr('Scan ongoing', level=2)
        post = Duration(OCR_ASSIGNMENT_REPORT_TIME)
        for group in [
            KEYWORDS_ASSIGNMENT_GROUP.Character_Materials,
            KEYWORDS_ASSIGNMENT_GROUP.EXP_Materials_Credits,
            KEYWORDS_ASSIGNMENT_GROUP.Synthesis_Materials,
        ]:
            self.goto_group(group)
            # goto_group includes load_rows, we just get remain time from cache
            dict_remain: "dict[AssignmentEntry, str]" = ASSIGNMENT_ENTRY_LIST.ocr.dict_remain
            current = now()
            for assignment, remain in dict_remain.items():
                remain = post.after_process(remain)
                remain = post.format_result(remain)
                if remain.total_seconds() > 0:
                    future = current + remain
                    logger.info(f'Assignment ongoing, will finish at {future}')
                    self.dispatched[assignment] = future
            # Can only have 4 at max
            if len(self.dispatched) >= 4:
                break
