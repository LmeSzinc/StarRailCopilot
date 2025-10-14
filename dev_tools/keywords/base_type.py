from dev_tools.keywords.base import GenerateKeyword, text_to_variable
from module.base.decorator import cached_property
from module.base.singleton import Singleton


class BaseType(GenerateKeyword, metaclass=Singleton):
    @cached_property
    def dict_internal_to_path(self):
        """
        Dict that convert internal path name to official path name

          {
            "ID": "Warrior",
            "BaseTypeIcon": "SpriteOutput/AvatarProfessionTattoo/Profession/BgPathsWarrior.png",
            ...
            "BaseTypeText": {
              "Hash": 10116566940563878966
            },
            "BaseTypeDesc": {
              "Hash": 1812126894190082015
            },
            "FirstWordText": "Destruction"
          },
        """
        out = {}
        data = self.read_file('./ExcelOutput/AvatarBaseType.json')
        for row in data:
            internal = row.get('ID', '')
            path = row.get('FirstWordText', '')
            if not internal or not path:
                continue
            out[internal] = text_to_variable(path)
        return out
