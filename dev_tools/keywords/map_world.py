import typing as t

from dev_tools.keywords.base import GenerateKeyword


class GenerateMapWorld(GenerateKeyword):
    output_file = './tasks/map/keywords/world.py'

    def iter_keywords(self) -> t.Iterable[dict]:

        def to_id(name):
            return self.find_keyword(name, lang='en')[0]

        yield dict(
            text_id=to_id('Herta Space Station'),
            world_id=0,
            short_name='Herta'
        )
        yield dict(
            text_id=to_id('Jarilo-VI'),
            world_id=1,
            short_name='Jarilo'
        )
        yield dict(
            text_id=to_id('The Xianzhou Luofu'),
            world_id=2,
            short_name='Luofu'
        )
        yield dict(
            text_id=to_id('Penacony'),
            world_id=3,
            short_name='Penacony'
        )
        yield dict(
            text_id=to_id('Amphoreus'),
            world_id=4,
            short_name='Amphoreus'
        )
        yield dict(
            text_id=self.find_keyword('二相乐园', lang='cn')[0],
            world_id=5,
            short_name='Planarcadia'
        )
