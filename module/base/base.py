from concurrent.futures import ThreadPoolExecutor

import module.config.server as server_
from module.base.button import Button, ButtonWrapper, ClickButton, match_template
from module.base.timer import Timer
from module.base.utils import *
from module.config.config import AzurLaneConfig
from module.device.device import Device
from module.logger import logger
from module.webui.setting import cached_class_property


class ModuleBase:
    config: AzurLaneConfig
    device: Device

    def __init__(self, config, device=None, task=None):
        """
        Args:
            config (AzurLaneConfig, str):
                Name of the user config under ./config
            device (Device, str):
                To reuse a device.
                If None, create a new Device object.
                If str, create a new Device object and use the given device as serial.
            task (str):
                Bind a task only for dev purpose. Usually to be None for auto task scheduling.
                If None, use default configs.
        """
        if isinstance(config, AzurLaneConfig):
            self.config = config
        elif isinstance(config, str):
            self.config = AzurLaneConfig(config, task=task)
        else:
            logger.warning('Alas ModuleBase received an unknown config, assume it is AzurLaneConfig')
            self.config = config

        if isinstance(device, Device):
            self.device = device
        elif device is None:
            self.device = Device(config=self.config)
        elif isinstance(device, str):
            self.config.override(Emulator_Serial=device)
            self.device = Device(config=self.config)
        else:
            logger.warning('Alas ModuleBase received an unknown device, assume it is Device')
            self.device = device

        self.interval_timer = {}

    @cached_class_property
    def worker(self) -> ThreadPoolExecutor:
        """
        A thread pool to run things at background
        """
        logger.hr('Creating worker')
        pool = ThreadPoolExecutor(1)
        return pool

    def match_template(self, button, interval=0, similarity=0.85):
        """
        Args:
            button (ButtonWrapper):
            interval (int, float): interval between two active events.
            similarity (int, float): 0 to 1.

        Returns:
            bool:

        Examples:
            Image detection:
            ```
            self.device.screenshot()
            self.appear(Button(area=(...), color=(...), button=(...))
            self.appear(Template(file='...')
            ```
        """
        self.device.stuck_record_add(button)

        if interval and not self.interval_is_reached(button, interval=interval):
            return False

        appear = button.match_template(self.device.image, similarity=similarity)

        if appear and interval:
            self.interval_reset(button, interval=interval)

        return appear

    def match_color(self, button, interval=0, threshold=10):
        """
        Args:
            button (ButtonWrapper):
            interval (int, float): interval between two active events.
            threshold (int): 0 to 255, smaller means more similar

        Returns:
            bool:
        """
        self.device.stuck_record_add(button)

        if interval and not self.interval_is_reached(button, interval=interval):
            return False

        appear = button.match_color(self.device.image, threshold=threshold)

        if appear and interval:
            self.interval_reset(button, interval=interval)

        return appear

    def match_template_color(self, button, interval=0, similarity=0.85, threshold=30):
        """
        Args:
            button (ButtonWrapper):
            interval (int, float): interval between two active events.
            similarity (int, float): 0 to 1.
            threshold (int): 0 to 255, smaller means more similar

        Returns:
            bool:
        """
        self.device.stuck_record_add(button)

        if interval and not self.interval_is_reached(button, interval=interval):
            return False

        appear = button.match_template_color(self.device.image, similarity=similarity, threshold=threshold)

        if appear and interval:
            self.interval_reset(button, interval=interval)

        return appear

    appear = match_template

    def appear_then_click(self, button, interval=5, similarity=0.85):
        appear = self.appear(button, interval=interval, similarity=similarity)
        if appear:
            self.device.click(button)
        return appear

    def wait_until_stable(self, button, timer=Timer(0.3, count=1), timeout=Timer(5, count=10)):
        """
        A terrible method, don't rely too much on it.
        """
        logger.info(f'Wait until stable: {button}')
        prev_image = self.image_crop(button)
        timer.reset()
        timeout.reset()
        while 1:
            self.device.screenshot()

            if timeout.reached():
                logger.warning(f'wait_until_stable({button}) timeout')
                break

            image = self.image_crop(button)
            if match_template(image, prev_image):
                if timer.reached():
                    logger.info(f'{button} stabled')
                    break
            else:
                prev_image = image
                timer.reset()

    def image_crop(self, button, copy=True):
        """Extract the area from image.

        Args:
            button(Button, tuple): Button instance or area tuple.
            copy:
        """
        if isinstance(button, Button):
            return crop(self.device.image, button.area, copy=copy)
        elif isinstance(button, ButtonWrapper):
            return crop(self.device.image, button.area, copy=copy)
        elif hasattr(button, 'area'):
            return crop(self.device.image, button.area, copy=copy)
        else:
            return crop(self.device.image, button, copy=copy)

    def image_color_count(self, button, color, threshold=221, count=50):
        """
        Args:
            button (Button, tuple): Button instance or area.
            color (tuple): RGB.
            threshold: 255 means colors are the same, the lower the worse.
            count (int): Pixels count.

        Returns:
            bool:
        """
        if isinstance(button, np.ndarray):
            image = button
        else:
            image = self.image_crop(button, copy=False)
        mask = color_similarity_2d(image, color=color)
        cv2.inRange(mask, threshold, 255, dst=mask)
        sum_ = cv2.countNonZero(mask)
        return sum_ > count

    def image_color_button(self, area, color, color_threshold=250, encourage=5, name='COLOR_BUTTON'):
        """
        Find an area with pure color on image, convert into a Button.

        Args:
            area (tuple[int]): Area to search from
            color (tuple[int]): Target color
            color_threshold (int): 0-255, 255 means exact match
            encourage (int): Radius of button
            name (str): Name of the button

        Returns:
            Button: Or None if nothing matched.
        """
        image = color_similarity_2d(self.image_crop(area), color=color)
        points = np.array(np.where(image > color_threshold)).T[:, ::-1]
        if points.shape[0] < encourage ** 2:
            # Not having enough pixels to match
            return None

        point = fit_points(points, mod=image_size(image), encourage=encourage)
        point = ensure_int(point + area[:2])
        button_area = area_offset((-encourage, -encourage, encourage, encourage), offset=point)
        return ClickButton(area=button_area, name=name)

    def get_interval_timer(self, button, interval=5, renew=False) -> Timer:
        if hasattr(button, 'name'):
            name = button.name
        elif callable(button):
            name = button.__name__
        else:
            name = str(button)

        try:
            timer = self.interval_timer[name]
            if renew and timer.limit != interval:
                timer = Timer(interval)
                self.interval_timer[name] = timer
            return timer
        except KeyError:
            timer = Timer(interval)
            self.interval_timer[name] = timer
            return timer

    def interval_reset(self, button, interval=5):
        if isinstance(button, (list, tuple)):
            for b in button:
                self.interval_reset(b, interval)
            return

        if button is not None:
            self.get_interval_timer(button, interval=interval).reset()

    def interval_clear(self, button, interval=5):
        if isinstance(button, (list, tuple)):
            for b in button:
                self.interval_clear(b, interval)
            return

        if button is not None:
            self.get_interval_timer(button, interval=interval).clear()

    def interval_is_reached(self, button, interval=5):
        return self.get_interval_timer(button, interval=interval, renew=True).reached()

    _image_file = ''

    @property
    def image_file(self):
        return self._image_file

    @image_file.setter
    def image_file(self, value):
        """
        For development.
        Load image from local file system and set it to self.device.image
        Test an image without taking a screenshot from emulator.
        """
        if isinstance(value, Image.Image):
            value = np.array(value)
        elif isinstance(value, str):
            value = load_image(value)

        self.device.image = value

    def set_lang(self, lang):
        """
        For development.
        Change lang and affect globally,
        including assets and server specific methods.
        """
        server_.set_lang(lang)
        logger.attr('Lang', self.config.LANG)

    def screenshot_tracking_add(self):
        """
        Add a tracking image, image will be saved
        """
        if not self.config.Error_SaveError:
            return

        logger.info('screenshot_tracking_add')
        data = self.device.screenshot_deque[-1]
        image = data['image']
        now = data['time']

        def image_encode(im, ti):
            import io
            from module.handler.sensitive_info import handle_sensitive_image

            output = io.BytesIO()
            im = handle_sensitive_image(im)
            Image.fromarray(im, mode='RGB').save(output, format='png')
            output.seek(0)

            self.device.screenshot_tracking.append({
                'time': ti,
                'image': output
            })

        ModuleBase.worker.submit(image_encode, image, now)
