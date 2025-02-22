import re
from typing import Dict

from module.config.server import VALID_LANG
from module.config.utils import read_file, write_file
from module.logger import logger
from tasks.relics.dev.base import Font, GeneratorBase
from tasks.relics.keywords import RelicSet, mainstat, relicpart, substat


class RelicSetKeywordGenerator(GeneratorBase):
    @classmethod
    def _is_keyword_valid(cls, dic_keyword: Dict[str, str], text: str, keyword: str):
        """
        A valid keyword must be a unique word in all text.
        """
        for t, kw in dic_keyword.items():
            if t == text:
                if keyword not in t:
                    return False
            else:
                if keyword in t:
                    return False
        return True

    @classmethod
    def _iter_wordpiece_from_text(cls, text: str, is_latin: bool):
        if is_latin:
            for w in re.split(r'[ \-—]', text):
                w = w.strip(',.:;[]')
                if len(w) >= 5:
                    yield w
        else:
            try:
                for a, b in zip(text[:-1], text[1:]):
                    yield a + b
            except IndexError:
                return

    @classmethod
    def _iter_word_from_text(cls, text: str, lang: str):
        """
        Iter all words to try from a given text
        """
        if lang == 'cn':
            for word in cls._iter_wordpiece_from_text(text, is_latin=False):
                if '的' in word:
                    continue
                yield word
            return
        if lang == 'en':
            for word in cls._iter_wordpiece_from_text(text, is_latin=True):
                yield word
            return
        raise NotImplementedError

    @classmethod
    def _update_keyword(cls, old_keyword: Dict[str, str], lang: str) -> Dict[str, str]:
        # Update relic sets in keywords
        dic_keyword = {}
        for relicset in RelicSet.instances.values():
            text = getattr(relicset, lang)
            keyword = old_keyword.get(text, '')
            dic_keyword[text] = keyword

        for text, keyword in dic_keyword.items():
            if keyword:
                # Existing keyword, test if valid:
                if not cls._is_keyword_valid(dic_keyword, text, keyword):
                    logger.warning(f'Relic set keyword is not globally unique: text="{text}", keyword="{keyword}"')
            else:
                # Empty keyword, try to generate one
                for word in cls._iter_word_from_text(text, lang=lang):
                    if cls._is_keyword_valid(dic_keyword, text, word):
                        dic_keyword[text] = keyword = word
                        break
                if not keyword:
                    logger.warning(f'Cannot find globally unique keyword: text="{text}"')
        return dic_keyword

    @classmethod
    def relicset_data(
            cls,
            output='./tasks/relics/dev/relic_keyword.json',
    ):
        data = read_file(output)
        for lang in VALID_LANG:
            old = data.get(lang, {})
            data[lang] = cls._update_keyword(old, lang)
        write_file(output, data)


class RelicRecGenerator(GeneratorBase):
    @staticmethod
    def rec_main_cn(
            file='zh-cn.ttf',
            output='./assets/cn/relics/rec_main',
            size=22,
    ):
        dict_text = {
            mainstat.HP: '生命',
            mainstat.ATK: '攻击',
            mainstat.DEF: '防御',
            mainstat.EffectHitRate: '效果',
            mainstat.OutgoingHealingBoost: '治疗',
            mainstat.CRITRate: '击率',
            mainstat.CRITDMG: '击伤',
            mainstat.SPD: '速度',
            mainstat.PhysicalDMGBoost: '物理',
            mainstat.FireDMGBoost: '火属',
            mainstat.IceDMGBoost: '冰属',
            mainstat.WindDMGBoost: '风属',
            mainstat.LightningDMGBoost: '雷属',
            mainstat.QuantumDMGBoost: '量子',
            mainstat.ImaginaryDMGBoost: '虚数',
            mainstat.BreakEffect: '击破',
            mainstat.EnergyRegenerationRate: '能量',
        }
        Font.clear_output(output)
        for stat, text in dict_text.items():
            out = f'{output}/{stat.name}.png'
            Font(file, size).draw(text, out)

    @staticmethod
    def _rec_main_en(
            file='en-US.ttf',
            output='./assets/en/relics/rec_main',
            size=22,
    ):
        dict_text = {
            mainstat.HP: 'HP',
            mainstat.ATK: 'ATK',
            mainstat.DEF: 'DEF',
            mainstat.EffectHitRate: 'Hit',
            mainstat.OutgoingHealingBoost: 'Outgo',
            mainstat.CRITRate: 'CRIT Rate',
            mainstat.CRITDMG: 'CRIT DMG',
            mainstat.SPD: 'SPD',
            mainstat.PhysicalDMGBoost: 'Physi',
            mainstat.FireDMGBoost: 'Fire',
            mainstat.IceDMGBoost: 'Ice',
            mainstat.WindDMGBoost: 'Wind',
            mainstat.LightningDMGBoost: 'Light',
            mainstat.QuantumDMGBoost: 'Quant',
            mainstat.ImaginaryDMGBoost: 'Imagi',
            mainstat.BreakEffect: 'Break',
            mainstat.EnergyRegenerationRate: 'Energy',
        }

    @staticmethod
    def rec_sub_cn(
            file='zh-cn.ttf',
            output='./assets/cn/relics/rec_sub',
            size=18,
    ):
        dict_text = {
            substat.HP: '生命',
            substat.ATK: '攻击',
            substat.DEF: '防御',
            substat.CRITRate: '击率',
            substat.CRITDMG: '击伤',
            substat.SPD: '速度',
            substat.EffectHitRate: '命中',
            substat.EffectRES: '抵抗',
            substat.BreakEffect: '击破',
        }
        Font.clear_output(output)
        for stat, text in dict_text.items():
            out = f'{output}/{stat.name}.png'
            Font(file, size).draw(text, out)

    @staticmethod
    def rec_part_cn(
            file='zh-cn.ttf',
            output='./assets/cn/relics/rec_part',
            size=18,
    ):
        dict_text = {
            relicpart.Head: '头部',
            relicpart.Hand: '手部',
            relicpart.Body: '躯干',
            relicpart.Feet: '脚部',
            relicpart.PlanarSphere: '位面',
            relicpart.LinkRope: '连结',
        }
        Font.clear_output(output)
        for stat, text in dict_text.items():
            out = f'{output}/{stat.name}.png'
            Font(file, size).draw(text, out)

    @staticmethod
    def rec_set_cn(
            file='zh-cn.ttf',
            output='./assets/cn/relics/rec_set',
            size=20,
            lang='cn'
    ):
        Font.clear_output(output)
        data = read_file('./tasks/relics/dev/relic_keyword.json')
        dict_keyword = data.get(lang, {})
        for relicset in RelicSet.instances.values():
            text = getattr(relicset, lang)
            keyword = dict_keyword.get(text, '')
            if not keyword:
                continue
            out = f'{output}/{relicset.name}.png'
            Font(file, size).draw(keyword, out)


if __name__ == '__main__':
    RelicSetKeywordGenerator.generate()
    RelicRecGenerator.generate()
