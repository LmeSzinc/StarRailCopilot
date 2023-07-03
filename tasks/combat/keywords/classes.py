from dataclasses import dataclass
from typing import ClassVar

from module.ocr.keyword import Keyword


@dataclass(repr=False)
class SupportCharacterList(Keyword):
    instances: ClassVar = {}
    
    @property
    def is_JING_YUAN(self):
        return 'JING_YUAN' in self.name
    
    @property
    def is_ASTA(self):
        return 'ASTA' in self.name
    
    @property
    def is_BAILU(self):
        return 'BAILU' in self.name
    
    @property
    def is_BRONYA(self):
        return 'BRONYA' in self.name
    
    @property
    def is_CLARA(self):
        return 'CLARA' in self.name
    
    @property
    def is_DAN_HENG(self):
        return 'DAN_HENG' in self.name
    
    @property
    def is_GEPARD(self):
        return 'GEPARD' in self.name
    
    @property
    def is_HIMEKO(self):
        return 'HIMEKO' in self.name
    
    @property
    def is_LUOCHA(self):
        return 'LUOCHA' in self.name
    
    @property
    def is_MARCH_7TH(self):
        return 'MARCH_7TH' in self.name
    
    @property
    def is_SAMPO(self):
        return 'SAMPO' in self.name
    
    @property
    def is_SEELE(self):
        return 'SEELE' in self.name
    
    @property
    def is_SILVER_WOLF(self):
        return 'SILVER_WOLF' in self.name
    
    @property
    def is_SUSHANG(self):
        return 'SUSHANG' in self.name
    
    @property
    def is_TINGYUN(self):
        return 'TINGYUN' in self.name
    
    @property
    def is_TRAILBLAZER_FIRE(self):
        return 'TRAILBLAZER_FIRE' in self.name
    
    @property
    def is_TRAILBLAZER_PHYSICAL(self):
        return 'TRAILBLAZER_PHYSICAL' in self.name
    
    @property
    def is_WELT(self):
        return 'WELT' in self.name
    
    @property
    def is_YANGQING(self):
        return 'YANGQING' in self.name
    
    
    