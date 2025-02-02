import tasks.character.keywords.character_list as KEYWORDS_CHARACTER_LIST
import tasks.character.keywords.combat_type as KEYWORDS_COMBAT_TYPE
from tasks.character.keywords.character_list import *
from tasks.character.keywords.classes import CharacterList, CombatType

DICT_SORTED_RANGES = {
    # Mage, hit instantly, no trajectories
    'Mage': [
        RuanMei,
        DanHengImbibitorLunae,
        Welt,
        Aventurine,
        TheHerta,
        FuXuan,
        # Longer precast
        BlackSwan,
    ],
    # Mage, but character moved after attack
    'MageSecondary': [
        Yanqing,
    ],
    # Archer
    'Archer': [
        Boothill,
        Lingsha,
        Yukong,
        Moze,
        TopazNumby,
        March7thPreservation,
        Bronya,
        Asta,
        Pela,
        Qingque,
        # Slow bullet
        Robin,
        TrailblazerHarmony,
        TrailblazerRemembrance,
    ],
    # Archer, but her parabolic trajectory has 0% accuracy on moving targets
    'ArcherSecondary': [
        Natasha,
    ],
    # Melee
    # rest of the characters are classified as melee and will not be switched to
}
