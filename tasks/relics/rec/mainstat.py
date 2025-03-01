from typing import Any, Dict, Optional

from module.base.decorator import cached_property
from module.base.utils import crop, extract_letters
from module.logger import logger
from tasks.relics.assets.assets_relics_rec import REC_MAINSTAT
from tasks.relics.keywords import MainStat, mainstat
from tasks.relics.rec.base import MatchResult, RelicRecBase


class RecMainStat(RelicRecBase):
    @cached_property
    def assets_mainstat(self) -> Dict[MainStat, Any]:
        assets = [
            mainstat.HP,
            mainstat.ATK,
            mainstat.DEF,
            mainstat.EffectHitRate,
            mainstat.OutgoingHealingBoost,
            mainstat.CRITRate,
            mainstat.CRITDMG,
            mainstat.SPD,
            mainstat.PhysicalDMGBoost,
            mainstat.FireDMGBoost,
            mainstat.IceDMGBoost,
            mainstat.WindDMGBoost,
            mainstat.LightningDMGBoost,
            mainstat.QuantumDMGBoost,
            mainstat.ImaginaryDMGBoost,
            mainstat.BreakEffect,
            mainstat.EnergyRegenerationRate,
        ]
        return self.read_assets_folder(
            f'assets/{self.lang}/relics/rec_mainstat',
            assets,
        )

    def rec_mainstat(self, image) -> Optional[MatchResult[MainStat]]:
        """
        Get main stat from image
        """
        area = REC_MAINSTAT.area
        image = crop(image, area, copy=False)
        image = extract_letters(image, letter=(235, 161, 66), threshold=255)
        # from PIL import Image
        # Image.fromarray(image, mode='L').show()

        result = self.match_template(image, self.assets_mainstat)
        result.move_area_base(area)
        logger.attr('mainstat', result.to_log())
        if result:
            return result
        else:
            return None
