from tasks.base.ui import UI
from tasks.login.assets.assets_login_agreement import *


class AgreementHandler(UI):
    def handle_user_agreement(self):
        """
        Returns:
            bool: If clicked
        """
        # CN user agreement popup
        if self.appear_then_click(USER_AGREEMENT_ACCEPT, interval=3):
            return True
        # Oversea TOS
        if self.match_template_color(TOS_ACCEPT, interval=3):
            self.device.click(TOS_ACCEPT)
            return True
        if self.appear(TOS_AGREE_TEXT, interval=3):
            # Select checkbox
            if not self.image_color_count(TOS_AGREE_CHECKBOX, color=(254, 240, 108), count=20, threshold=180):
                self.device.click(TOS_AGREE_CHECKBOX)
                return True
        return False
