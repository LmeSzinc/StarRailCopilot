from dataclasses import dataclass
from typing import ClassVar

from module.ocr.keyword import Keyword

@dataclass(repr=False)
class CharacterList(Keyword):
    instances: ClassVar = {}
    
    @property
    def is_March_7th(self):
        return 'March_7th' in self.name
    
    @property
    def is_Dan_Heng(self):
        return 'Dan_Heng' in self.name
    
    @property
    def is_Pela(self):
        return 'Pela' in self.name
    
    @property
    def is_Tingyun(self):
        return 'Tingyun' in self.name
    
    @property
    def is_Clara(self):
        return 'Clara' in self.name
    
    @property
    def is_Himeko(self):
        return 'Himeko' in self.name
    
    @property
    def is_Natasha(self):
        return 'Natasha' in self.name
    
    @property
    def is_Bronya(self):
        return 'Bronya' in self.name
    
    @property
    def is_Seele(self):
        return 'Seele' in self.name
    
    @property
    def is_Serval(self):
        return 'Serval' in self.name
    
    @property
    def is_Yanqing(self):
        return 'Yanqing' in self.name
    
    @property
    def is_Jing_Yuan(self):
        return 'Jing_Yuan' in self.name
    
    @property
    def is_Gepard(self):
        return 'Gepard' in self.name
    
    @property
    def is_Sampo(self):
        return 'Sampo' in self.name
    
    @property
    def is_Welt(self):
        return 'Welt' in self.name
    
    @property
    def is_Bailu(self):
        return 'Bailu' in self.name
    
    @property
    def is_Sushang(self):
        return 'Sushang' in self.name
    
    @property
    def is_Luocha(self):
        return 'Luocha' in self.name
    
    @property
    def is_Asta(self):
        return 'Asta' in self.name
    
    @property
    def is_Hook(self):
        return 'Hook' in self.name
    
    @property
    def is_Silver_Wolf(self):
        return 'Silver_Wolf' in self.name
    
    @property
    def is_Arlan(self):
        return 'Arlan' in self.name
    
    @property
    def is_Qingque(self):
        return 'Qingque' in self.name
    
    @property
    def is_Yukong(self):
        return 'Yukong' in self.name
    
    @property
    def is_Herta(self):
        return 'Herta' in self.name