import argparse

from module.base.button import ClickButton
from module.base.timer import Timer
from module.base.utils import color_similar, get_color
from tasks.base.daemon import Daemon

TAKE_PHOTO = ClickButton((1101, 332, 1162, 387), name='TAKE_PHOTO')


class TrashBin(Daemon):
    def is_camera_active(self):
        color = get_color(self.device.image, (568, 358, 588, 362))
        if color_similar(color, (23, 254, 180), threshold=20):
            return True
        if color_similar(color, (225, 214, 124), threshold=30):
            return True
        return False

    def is_in_camera(self):
        # Green icon
        if self.image_color_count(TAKE_PHOTO, color=(134, 209, 187), threshold=221, count=200):
            # White background
            if self.image_color_count(TAKE_PHOTO, color=(235, 233, 237), threshold=221, count=1000):
                return True
        return False

    photo_interval = Timer(1)

    def handle_blessing(self):
        if self.photo_interval.reached():
            if self.is_in_camera() and self.is_camera_active():
                self.device.click(TAKE_PHOTO)
                self.photo_interval.reset()

    def run(self):
        self.device.disable_stuck_detection()
        self.device.screenshot_interval_set(0.05)
        _ = self.device.maatouch_builder
        super().run()


if __name__ == '__main__':
    """
    Do minigame in 2.4 (2024.08), taking photos of the trashbins
    
    To run this file:
        python -m tasks.minigame.trashbin
    Or:
        python -m tasks.minigame.trashbin <instance>
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('instance', nargs='?', default='src', help='SRC instance name')

    args = parser.parse_args()
    instance = args.instance

    src = TrashBin(instance)
    src.run()
