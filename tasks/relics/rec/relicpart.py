from typing import Any, Dict, Optional

from module.base.decorator import cached_property
from module.base.utils import crop, extract_letters
from module.logger import logger
from tasks.relics.assets.assets_relics_rec import REC_RELICPART
from tasks.relics.keywords import RelicPart, relicpart
from tasks.relics.rec.base import MatchResult, RelicRecBase


class RecRelicPart(RelicRecBase):
    @cached_property
    def assets_relicpart(self) -> Dict[RelicPart, Any]:
        assets = [
            relicpart.Head,
            relicpart.Hand,
            relicpart.Body,
            relicpart.Feet,
            relicpart.PlanarSphere,
            relicpart.LinkRope,
        ]
        return self.read_assets_folder(
            f'assets/{self.lang}/relics/rec_relicpart',
            assets,
        )

    def rec_relicpart(self, image) -> Optional[MatchResult[RelicPart]]:
        """
        Get relic part from image
        """
        area = REC_RELICPART.area
        image = crop(image, area, copy=False)
        image = extract_letters(image, letter=(255, 255, 255), threshold=255)
        # from PIL import Image
        # Image.fromarray(image, mode='L').show()

        result = self.match_template(image, self.assets_relicpart)
        logger.attr('relicpart', result.to_log())
        if result:
            return result
        else:
            return None
