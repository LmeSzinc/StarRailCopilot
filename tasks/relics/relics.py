from module.logger import logger
from tasks.relics.reinforce import RelicsReinforce
from tasks.relics.salvage import RelicsSalvage

class Relics(RelicsSalvage,RelicsReinforce):
    def organize(self,):
        raise NotImplementedError