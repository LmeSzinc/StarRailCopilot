
from tasks.relics.dev.base import Font, GeneratorBase
from tasks.relics.keywords import substat, mainstat


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


if __name__ == '__main__':
    RelicRecGenerator.generate()
