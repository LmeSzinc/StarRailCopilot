from module.base.decorator import cached_property
from module.logger import logger
from tasks.base.ui import UI


class PlannerLang(UI):
    @cached_property
    def planner_lang(self):
        """
        Planner web language depends on game package, not user setting

        Returns:
            str:
        """
        if self.config.Emulator_PackageName in ['CN-Official', 'CN-Bilibili']:
            lang = 'cn'
        elif self.config.Emulator_PackageName in [
            'OVERSEA-America', 'OVERSEA-Asia', 'OVERSEA-Europe', 'OVERSEA-TWHKMO']:
            lang = 'en'
        else:
            lang = self.config.LANG
            if lang == 'auto':
                logger.error('Language was not set before planner scan, assume it is "cn"')
                lang = 'cn'
        logger.attr('PlannerLang', lang)
        return lang
