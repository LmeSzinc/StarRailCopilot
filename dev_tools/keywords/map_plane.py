import typing as t

from dev_tools.keywords.base import GenerateKeyword, TextMap
from module.base.decorator import cached_property
from module.config.utils import deep_get


class GenerateMapPlane(GenerateKeyword):
    output_file = './tasks/map/keywords/plane.py'

    @cached_property
    def AreaMapConfig(self):
        return self.read_file('./ExcelOutput/AreaMapConfig.json')

    @cached_property
    def NavMapTab(self):
        rows = self.read_file('./ExcelOutput/NavMapTab.json')
        data = {}
        for row in rows:
            plane_id = int(deep_get(row, 'ID', 0))
            data[plane_id] = row
        return data

    @cached_property
    def MazePlane(self):
        rows = self.read_file('./ExcelOutput/MazePlane.json')
        data = {}
        for row in rows:
            floors = deep_get(row, 'FloorIDList', [])
            if floors and len(floors) == 1:
                plane_id = floors[0]
            else:
                plane_id = int(deep_get(row, 'StartFloorID', 0))
            data[plane_id] = row
        return data

    def iter_planes_v20(self) -> t.Iterable[dict]:
        dic_hardcoded_text = {
            # 观景车厢
            1000001: 1731188599,
            # 客房车厢
            1000002: 2134473126,
            # 派对车厢
            1000003: 1905536184,
            # 金人巷
            1020204: 1146019185,
        }
        for data in self.AreaMapConfig:
            plane_id = int(deep_get(data, 'ID', 0))
            world_id = int(str(plane_id)[-5])
            sort_id = int(deep_get(data, 'MenuSortID', 0))
            text_id = deep_get(data, 'Name.Hash')

            if plane_id <= 1000000:
                continue

            # Redirect to names in MapPlane
            try:
                p = plane_id // 10 * 100 + plane_id % 10
                maze_data = self.MazePlane[p]
                text_id = deep_get(maze_data, ['PlaneName', 'Hash'], default=0)
                # text = self.find_keyword(text_id, lang='cn')[1]
                # print(world_id, maze_data, plane_id, text_id, text)
            except KeyError:
                # print(world_id, plane_id, text_id)
                text_id = dic_hardcoded_text.get(plane_id, text_id)
            yield dict(
                text_id=text_id,
                world_id=world_id,
                plane_id=plane_id,
                sort_id=sort_id,
            )

    def iter_planes_v30(self) -> t.Iterable[dict]:
        for data in self.MazePlane.values():
            plane_type = deep_get(data, ['PlaneType'], default='')
            if plane_type not in ['Town', 'Maze', 'Train']:
                continue
            plane_id = deep_get(data, ['StartFloorID'], default=0)
            text_id = deep_get(data, ['PlaneName', 'Hash'], default=0)
            text = self.find_keyword(text_id, lang='cn')[1]
            # {TEXTJOIN#87}
            if 'TEXTJOIN#' in text:
                continue
            if plane_id <= 10000000:
                continue

            world_id = deep_get(data, ['WorldID'], default=-1)
            if world_id >= 100:
                world_id = int(world_id // 100) - 1
            try:
                sort_id = self.NavMapTab[plane_id]['SortID']
            except KeyError:
                # print(world_id, plane_id, text_id, text)
                continue

            # 20331001 -> 2033101
            plane_id = int(plane_id // 10 + plane_id % 10)
            yield dict(
                text_id=text_id,
                world_id=world_id,
                plane_id=plane_id,
                sort_id=sort_id,
            )

    def iter_planes(self):
        rows = {}
        for data in self.iter_planes_v20():
            rows[data['plane_id']] = data
        for data in self.iter_planes_v30():
            rows.setdefault(data['plane_id'], data)
        for data in rows.values():
            yield data

    def iter_keywords(self) -> t.Iterable[dict]:
        """
        20123001
             ^^^ floor
           ^^ plane
          ^ world
        """

        def to_id(name):
            return self.find_keyword(name, lang='cn')[0]

        domains = ['黑塔的办公室', '锋芒崭露']
        for index, domain in enumerate(domains):
            yield dict(
                text_id=to_id(domain),
                world_id=-1,
                plane_id=index + 1,
            )
        domains = ['区域-战斗', '区域-事件', '区域-遭遇', '区域-休整', '区域-精英', '区域-首领', '区域-交易']
        for index, domain in enumerate(domains):
            yield dict(
                text_id=to_id(domain),
                world_id=-2,
                plane_id=index + 1,
            )
        domains = ['晖长石号', '开拓之尾号', '塔塔洛夫号', '飞翔时针号']
        for index, domain in enumerate(domains):
            yield dict(
                text_id=to_id(domain),
                world_id=3,
                plane_id=index + 1,
            )

        keywords = sorted(self.iter_planes(), key=lambda x: (x['world_id'], x['sort_id']))
        for keyword in keywords:
            keyword.pop('sort_id')
            yield keyword

    def convert_name(self, text: str, keyword: dict) -> str:
        text = super().convert_name(text, keyword=keyword)
        text = text.replace('_', '')
        if not text:
            return ""
        from tasks.map.keywords import MapWorld
        world = MapWorld.find_world_id(keyword['world_id'])
        if world is None:
            if text.startswith('Domain'):
                return f'Rogue_{text}'
            else:
                return f'Special_{text}'
        else:
            return f'{world.short_name}_{text}'

    def convert_keyword(self, text: str, lang: str) -> str:
        text = text.replace('™', '')
        return super().convert_keyword(text, lang=lang)


if __name__ == '__main__':
    import os

    os.chdir(os.path.join(os.path.dirname(__file__), '../../'))
    TextMap.DATA_FOLDER = '../turnbasedgamedata'
    self = GenerateMapPlane()
