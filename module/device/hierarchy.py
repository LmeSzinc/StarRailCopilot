import re

from lxml import etree

from module.base.decorator import cached_property


class HierarchyButton:
    """
    Convert UI hierarchy to an object like the Button in Alas.
    """
    _name_regex = re.compile('@.*?=[\'\"](.*?)[\'\"]')

    def __init__(self, hierarchy: etree._Element, xpath: str):
        self.hierarchy = hierarchy
        self.xpath = xpath
        self.nodes = hierarchy.xpath(xpath)

    @cached_property
    def name(self):
        res = HierarchyButton._name_regex.findall(self.xpath)
        if res:
            return res[0]
        else:
            return self.xpath

    @cached_property
    def count(self):
        return len(self.nodes)

    @cached_property
    def exist(self):
        return self.count == 1

    @cached_property
    def attrib(self):
        if self.exist:
            return self.nodes[0].attrib
        else:
            return {}

    @cached_property
    def area(self):
        if self.exist:
            bounds = self.attrib.get("bounds")
            lx, ly, rx, ry = map(int, re.findall(r"\d+", bounds))
            return lx, ly, rx, ry
        else:
            return None

    @cached_property
    def size(self):
        if self.area is not None:
            lx, ly, rx, ry = self.area
            return rx - lx, ry - ly
        else:
            return None

    @cached_property
    def button(self):
        return self.area

    def __bool__(self):
        return self.exist

    def __str__(self):
        return self.name

    """
    Element props
    """

    def _get_bool_prop(self, prop: str) -> bool:
        return self.attrib.get(prop, "").lower() == 'true'

    @cached_property
    def index(self) -> int:
        try:
            return int(self.attrib.get("index", 0))
        except IndexError:
            return 0

    @cached_property
    def text(self) -> str:
        return self.attrib.get("text", "").strip()

    @cached_property
    def resourceId(self) -> str:
        return self.attrib.get("resourceId", "").strip()

    @cached_property
    def package(self) -> str:
        return self.attrib.get("resourceId", "").strip()

    @cached_property
    def description(self) -> str:
        return self.attrib.get("resourceId", "").strip()

    @cached_property
    def checkable(self) -> bool:
        return self._get_bool_prop('checkable')

    @cached_property
    def clickable(self) -> bool:
        return self._get_bool_prop('clickable')

    @cached_property
    def enabled(self) -> bool:
        return self._get_bool_prop('enabled')

    @cached_property
    def fucusable(self) -> bool:
        return self._get_bool_prop('fucusable')

    @cached_property
    def focused(self) -> bool:
        return self._get_bool_prop('focused')

    @cached_property
    def scrollable(self) -> bool:
        return self._get_bool_prop('scrollable')

    @cached_property
    def longClickable(self) -> bool:
        return self._get_bool_prop('longClickable')

    @cached_property
    def password(self) -> bool:
        return self._get_bool_prop('password')

    @cached_property
    def selected(self) -> bool:
        return self._get_bool_prop('selected')
