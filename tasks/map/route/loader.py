import importlib
import os

from module.base.decorator import del_cached_property
from module.exception import GameStuckError, GameTooManyClickError, ScriptError
from module.logger import logger
from tasks.base.ui import UI
from tasks.map.route.base import RouteBase
from tasks.map.route.model import RouteModel


def empty_function(*arg, **kwargs):
    return False


class RouteLoader(UI):
    route_module: str = ''
    route_func: str = ''
    route_obj: RouteBase

    def route_delete(self):
        del_cached_property(self, 'route_obj')
        self.route_module = ''
        self.route_func = ''

    def route_run(self, route: RouteModel | str):
        """
        Args:
            route: .py module path such as `route.daily.ForgottenHallStage1:route`
                which will load `./route/daily/ForgottenHallStage1.py` and run `Route.route()`
        """
        logger.hr('Route run', level=1)
        if isinstance(route, RouteModel):
            route = route.route
        logger.attr('Route', route)
        try:
            module, func = route.split(':')
        except ValueError:
            logger.critical(f'Route invalid: {route}')
            raise ScriptError
        path = f'./{module.replace(".", "/")}.py'

        # Import route file
        try:
            module_obj = importlib.import_module(f'{module}')
        except ModuleNotFoundError:
            logger.critical(f'Route file not found: {module} ({path})')
            if not os.path.exists(path):
                logger.critical(f'Route file not exists: {path}')
            raise ScriptError

        # Create route object
        # Reuse the previous one
        if self.route_module != module:
            # config = copy.deepcopy(self.config).merge(module.Config())
            config = self.config
            device = self.device
            try:
                self.route_obj = module_obj.Route(config=config, device=device)
            except AttributeError as e:
                logger.critical(e)
                logger.critical(f'Route file {route} ({path}) must define class Route')
                raise ScriptError
            self.route_module = module
            self.route_obj.route_module = module

        self.route_obj.plane = self.plane
        self.device.screenshot_tracking.clear()

        # before_route()
        try:
            before_func_obj = self.route_obj.__getattribute__('before_route')
        except AttributeError:
            before_func_obj = empty_function
        try:
            before_func_obj()
        except (GameStuckError, GameTooManyClickError):
            logger.error(f'Route failed: {route}')
            raise

        # Run route
        try:
            func_obj = self.route_obj.__getattribute__(func)
        except AttributeError as e:
            logger.critical(e)
            logger.critical(f'Route class in {route} ({path}) does not have method {func}')
            raise ScriptError
        self.route_func = func
        self.route_obj.route_func = func
        try:
            func_obj()
        except (GameStuckError, GameTooManyClickError):
            logger.error(f'Route failed: {route}')
            raise

        # after_route()
        try:
            after_route_obj = self.route_obj.__getattribute__('after_route')
        except AttributeError:
            after_route_obj = empty_function
        try:
            after_route_obj()
        except (GameStuckError, GameTooManyClickError):
            logger.error(f'Route failed: {route}')
            raise

        self.device.screenshot_tracking.clear()
