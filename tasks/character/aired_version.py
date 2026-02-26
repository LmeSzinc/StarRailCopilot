from tasks.character.keywords.character_list import *

dict_aired_version = {
    # Trailblazer
    TrailblazerDestruction: "0.0",
    TrailblazerPreservation: "0.0",
    TrailblazerHarmony: "0.0",
    TrailblazerRemembrance: "0.0",

    # 0.0
    Himeko: "0.0",
    Welt: "0.0",
    Gepard: "0.0",
    Bronya: "0.0",
    Clara: "0.0",
    Yanqing: "0.0",
    Bailu: "0.0",

    March7thPreservation: "0.0",
    DanHeng: "0.0",
    Asta: "0.0",
    Serval: "0.0",
    Herta: "0.0",
    Qingque: "0.0",
    Sushang: "0.0",
    Hook: "0.0",
    Arlan: "0.0",
    Sampo: "0.0",
    Tingyun: "0.0",
    Pela: "0.0",
    Natasha: "0.0",

    Seele: "1.0",
    JingYuan: "1.0",
    SilverWolf: "1.1",
    Luocha: "1.1",
    Yukong: "1.1",
    Blade: "1.2",
    Kafka: "1.2",
    Luka: "1.2",
    DanHengImbibitorLunae: "1.3",
    FuXuan: "1.3",
    Lynx: "1.3",
    Jingliu: "1.4",
    TopazNumby: "1.4",
    Guinaifen: "1.4",
    Huohuo: "1.5",
    Argenti: "1.5",
    Hanya: "1.5",
    RuanMei: "1.6",
    DrRatio: "1.6",
    Xueyi: "1.6",

    # 2.0
    BlackSwan: "2.0",
    Sparkle: "2.0",
    Misha: "2.0",
    Acheron: "2.1",
    Aventurine: "2.1",
    Gallagher: "2.1",
    Robin: "2.2",
    Boothill: "2.2",
    Firefly: "2.3",
    Jade: "2.3",
    Yunli: "2.4",
    March7thTheHunt: "2.4",
    Jiaoqiu: "2.4",
    Feixiao: "2.5",
    Lingsha: "2.5",
    Moze: "2.5",
    Rappa: "2.6",
    Sunday: "2.7",
    Fugue: "2.7",

    # 3.0
    TheHerta: "3.0",
    Aglaea: "3.0",
    Tribbie: "3.1",
    Mydei: "3.1",
    Castorice: "3.2",
    Anaxa: "3.2",
    Hyacine: "3.3",
    Cipher: "3.3",
    Phainon: "3.4",
    Saber: "3.4",
    Archer: "3.4",
    Hysilens: "3.5",
    Cerydra: "3.5",
    Evernight: "3.6",
    DanHengPermansorTerrae: "3.6",
    Cyrene: "3.7",
    TheDahlia: "3.8",
    Sparxie: "4.0",
    YaoGuang: "4.0",
}


def sort_dict_by_version_desc():
    version_groups = {}
    for idx, (key, value) in enumerate(dict_aired_version.items()):
        if value not in version_groups:
            version_groups[value] = []
        version_groups[value].append((key, idx))

    sorted_versions = sorted(version_groups.keys(), key=lambda x: [float(part) for part in x.split('.')], reverse=True)

    sorted_dict = {}
    for version in sorted_versions:
        items = sorted(version_groups[version], key=lambda x: x[1])
        for key, _ in items:
            sorted_dict[key] = version

    return sorted_dict


def list_support_characters() -> "list[CharacterList]":
    """
    List of characters to insert into character support list
    """
    out = {}
    for character, version in sort_dict_by_version_desc().items():
        out[character] = version
    for character in CharacterList.instances.values():
        if character not in out:
            print(f'WARNING | Character {character} is not in dict_aired_version, please define it manually')
            out[character] = ''
    return list(out)


def get_character_version(character: "CharacterList | str") -> str:
    if isinstance(character, str):
        try:
            character = CharacterList.instances[character]
        except KeyError:
            return ''
    version = dict_aired_version.get(character, '')
    if version == '0.0':
        version = ''
    return version


if __name__ == '__main__':
    for k in list_support_characters():
        print(k)
