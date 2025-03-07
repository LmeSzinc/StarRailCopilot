from dataclasses import dataclass
from typing import List, Optional, Tuple

from module.base.utils import load_image
from module.logger import logger
from tasks.relics.keywords import MainStat, RelicPart, RelicSet, SubStat, substat
from tasks.relics.rec.mainstat import RecMainStat
from tasks.relics.rec.reliclevel import RecRelicLevel
from tasks.relics.rec.relicpart import RecRelicPart
from tasks.relics.rec.relicset import RecRelicSet
from tasks.relics.rec.substat import RecSubStat


@dataclass
class SubStatResult:
    name: SubStat
    value: float

    def to_log(self):
        return f'{self.name.name}={self.value}'


@dataclass
class RelicRecResult:
    relicset: RelicSet
    relicpart: RelicPart
    reliclevel: int
    mainstat: MainStat
    substat: List[SubStatResult]

    def to_log(self):
        sub = [s.to_log() for s in self.substat]
        sub = f'[{",".join(sub)}]'
        info = [
            self.relicset.name,
            self.relicpart.name,
            str(self.reliclevel),
            self.mainstat.name,
            sub,
        ]
        info = f'({", ".join(info)})'
        return info


def get_center_y(area: Tuple[int, int, int, int]) -> float:
    return (area[1] + area[3]) / 2


class RelicRec(RecMainStat, RecSubStat, RecRelicPart, RecRelicSet, RecRelicLevel):
    def rec(self, image) -> Optional[RelicRecResult]:
        """
        Recognise a relic from image.

        This method should cost < 50ms
        """
        self.reset()

        # Do rec_relicset first to set relicset_top_y
        relicset = self.rec_relicset(image)
        if relicset is None:
            logger.warning(f'Invalid relic, empty relicset')
            return None

        relicpart = self.rec_relicpart(image)
        if relicpart is None:
            logger.warning(f'Invalid relic, empty relicpart')
            return None

        reliclevel = self.rec_reliclevel(image)
        if reliclevel < 0 or reliclevel > 15:
            logger.warning(f'Invalid relic, invalid reliclevel')
            return None

        mainstat = self.rec_mainstat(image)
        if mainstat is None:
            logger.warning(f'Invalid relic, empty mainstat')
            return None

        subname = self.rec_subname(image)
        subvalue = self.rec_subvalue(image)

        # Create a dictionary for subvalue with center y-coordinates
        value_y = {}
        for value in subvalue:
            y = get_center_y(value.area)
            value_y[y] = value
        # Find pairs with center y-coordinates differing by less than 10
        pairs = []
        for sub in subname:
            stat_center_y = get_center_y(sub.area)
            for y, value in value_y.items():
                if abs(stat_center_y - y) < 10:
                    pairs.append((sub, value))
                    break
            else:
                logger.warning(f'Invalid relic, substat has no value matched: {sub}')
                return None
        # Validate pairs
        substat_list = []
        for sub, value in pairs:
            sub = self._pair_sub_value(sub.result, value.result)
            # Mark invalid if any substat is invalid to avoid unexpected behaviour at relic filtering
            if sub is None:
                return None
            substat_list.append(sub)
        if reliclevel > 0 and not substat_list:
            logger.warning('Invalid relic, reliclevel > 0 but has not substat')
            return

        # Construct result
        result = RelicRecResult(
            relicset=relicset.result,
            relicpart=relicpart.result,
            reliclevel=reliclevel,
            mainstat=mainstat.result,
            substat=substat_list,
        )
        logger.attr('Relic', result.to_log())
        return result

    @staticmethod
    def _pair_sub_value(sub: SubStat, value: str) -> Optional[SubStatResult]:
        value_has_percent = '%' in value

        # Extract value
        v = value.replace('%', '')
        try:
            v = float(v)
        except ValueError:
            logger.warning(f'Invalid relic, subvalue is not a float: {v}')
            return None

        # Convert ATK, HP, DEF
        if sub == substat.ATK:
            if not value_has_percent:
                sub = substat.ATKd
        elif sub == substat.HP:
            if not value_has_percent:
                sub = substat.HPd
        elif sub == substat.DEF:
            if not value_has_percent:
                sub = substat.DEFd
        # Validate if value has %
        elif sub == substat.SPD:
            if value_has_percent:
                logger.warning(f'Invalid relic, substat SPD cannot in % ({sub}, {value})')
                return None
            v = int(v)
        else:
            if not value_has_percent:
                logger.warning(f'Invalid relic, substat {sub.name} cannot in % ({sub}, {value})')
                return None

        return SubStatResult(name=sub, value=v)


if __name__ == '__main__':
    self = RelicRec()
    # Paste your image file here
    f = r''
    i = load_image(f)
    r = self.rec(i)
