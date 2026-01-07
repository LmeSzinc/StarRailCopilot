import pytest

from tasks.planner.keywords.item_ascension import Broken_Teeth_of_Iron_Wolf
from tasks.planner.keywords.item_trace import Worldbreaker_Blade
from tasks.planner.model import StoredPlannerProxy, MultiValue


class TestUpdateSynthesize:
    """测试update_synthesize方法的各种合成情况"""

    @pytest.fixture
    def mock_item(self):
        """创建mock的item对象"""
        return Worldbreaker_Blade

    def create_proxy(self, mock_item, value_green=0, value_blue=0, value_purple=0,
                     total_green=0, total_blue=0, total_purple=0):
        """辅助方法：创建StoredPlannerProxy对象"""
        proxy = StoredPlannerProxy(
            item=mock_item,
            value=MultiValue(green=value_green, blue=value_blue, purple=value_purple),
            total=MultiValue(green=total_green, blue=total_blue, purple=total_purple),
            synthesize=MultiValue()
        )
        return proxy

    def test_strategy1_blue_to_purple(self, mock_item):
        """策略1: 使用溢出的蓝合成紫 (3蓝→1紫)"""
        # 有9个溢出的蓝，需要2个紫
        proxy = self.create_proxy(
            mock_item,
            value_green=0, value_blue=15, value_purple=0,
            total_green=0, total_blue=6, total_purple=2
        )

        proxy.update_synthesize()

        # 应该合成2个紫，消耗6个蓝
        assert proxy.synthesize.purple == 2
        assert proxy.synthesize.blue == 0  # 从蓝合成紫不记录syn_blue
        assert proxy.synthesize.green == 0

    def test_strategy2_green_to_purple_directly(self, mock_item):
        """策略2: 从绿直接合成紫 (9绿→1紫)"""
        # 有27个溢出的绿，需要2个紫
        proxy = self.create_proxy(
            mock_item,
            value_green=30, value_blue=0, value_purple=0,
            total_green=3, total_blue=0, total_purple=2
        )

        proxy.update_synthesize()

        # 应该合成2个紫，消耗18个绿
        assert proxy.synthesize.purple == 2
        assert proxy.synthesize.blue == 0  # 一步合成，不记录中间的蓝
        assert proxy.synthesize.green == 0

    def test_strategy3_mixed_green_blue_to_purple(self, mock_item):
        """策略3: 混合使用绿和蓝合成紫"""
        # 有5个溢出的蓝和9个溢出的绿，需要4个紫
        # 5个蓝可以合成1个紫（剩余2个蓝）
        # 需要再合成3个紫，需要9个蓝，现有2个蓝，还需7个蓝
        # 7个蓝需要21个绿，但只有9个绿，所以只能合成3个蓝
        # 2+3=5个蓝，可以再合成1个紫
        proxy = self.create_proxy(
            mock_item,
            value_green=12, value_blue=8, value_purple=0,
            total_green=3, total_blue=3, total_purple=4
        )

        proxy.update_synthesize()

        # 先用蓝合成：5个蓝→1个紫，剩2个蓝，还需3个紫
        # 然后用绿合成：9个绿可以用，2+3=5个蓝→1个紫，消耗9个绿
        # 总共合成2个紫
        assert proxy.synthesize.purple == 2
        assert proxy.synthesize.blue == 0  # 一步合成，不记录
        assert proxy.synthesize.green == 0

    def test_green_to_blue_when_blue_insufficient(self, mock_item):
        """当紫够但蓝不足时: 从绿合成蓝 (3绿→1蓝)"""
        # 有9个溢出的绿，紫够了，但缺3个蓝
        proxy = self.create_proxy(
            mock_item,
            value_green=15, value_blue=2, value_purple=10,
            total_green=6, total_blue=5, total_purple=5
        )

        proxy.update_synthesize()

        # 应该合成3个蓝，消耗9个绿
        assert proxy.synthesize.blue == 3
        assert proxy.synthesize.purple == 0
        assert proxy.synthesize.green == 0

    def test_no_overflow_no_synthesis(self, mock_item):
        """没有溢出材料时，不进行合成"""
        proxy = self.create_proxy(
            mock_item,
            value_green=5, value_blue=3, value_purple=2,
            total_green=10, total_blue=5, total_purple=3
        )

        proxy.update_synthesize()

        # 所有材料都不足，不应该合成
        assert proxy.synthesize.purple == 0
        assert proxy.synthesize.blue == 0
        assert proxy.synthesize.green == 0

    def test_priority_blue_over_green(self, mock_item):
        """测试优先使用蓝而不是绿"""
        # 有6个溢出的蓝和18个溢出的绿，需要2个紫
        proxy = self.create_proxy(
            mock_item,
            value_green=20, value_blue=10, value_purple=0,
            total_green=2, total_blue=4, total_purple=2
        )

        proxy.update_synthesize()

        # 应该优先用蓝：6个蓝→2个紫
        assert proxy.synthesize.purple == 2
        assert proxy.synthesize.blue == 0
        assert proxy.synthesize.green == 0

    def test_exact_amount_synthesis(self, mock_item):
        """测试精确数量的合成"""
        # 正好9个绿，需要1个紫
        proxy = self.create_proxy(
            mock_item,
            value_green=12, value_blue=0, value_purple=0,
            total_green=3, total_blue=0, total_purple=1
        )

        proxy.update_synthesize()

        assert proxy.synthesize.purple == 1
        assert proxy.synthesize.blue == 0
        assert proxy.synthesize.green == 0

    def test_insufficient_green_for_purple(self, mock_item):
        """测试绿材料不足9个时无法合成紫"""
        # 只有8个溢出的绿，需要1个紫
        proxy = self.create_proxy(
            mock_item,
            value_green=10, value_blue=0, value_purple=0,
            total_green=2, total_blue=0, total_purple=1
        )

        proxy.update_synthesize()

        # 8个绿不足以合成紫（需要9个）
        assert proxy.synthesize.purple == 0
        assert proxy.synthesize.blue == 0
        assert proxy.synthesize.green == 0

    def test_all_materials_overflow(self, mock_item):
        """测试所有材料都溢出时不需要合成"""
        proxy = self.create_proxy(
            mock_item,
            value_green=20, value_blue=10, value_purple=5,
            total_green=10, total_blue=5, total_purple=3
        )

        proxy.update_synthesize()

        # 所有材料都够，不需要合成
        assert proxy.synthesize.purple == 0
        assert proxy.synthesize.blue == 0
        assert proxy.synthesize.green == 0

    def test_large_numbers(self, mock_item):
        """测试大数量的合成"""
        # 有100个溢出的绿，需要10个紫
        proxy = self.create_proxy(
            mock_item,
            value_green=120, value_blue=0, value_purple=0,
            total_green=20, total_blue=0, total_purple=10
        )

        proxy.update_synthesize()

        # 100个绿可以合成11个紫，但只需要10个
        assert proxy.synthesize.purple == 10
        assert proxy.synthesize.blue == 0
        assert proxy.synthesize.green == 0

    def test_combined_strategies(self, mock_item):
        """测试多策略组合使用"""
        # 有4个溢出的蓝（可以合成1个紫）和27个溢出的绿（可以合成3个紫），需要3个紫
        proxy = self.create_proxy(
            mock_item,
            value_green=30, value_blue=7, value_purple=0,
            total_green=3, total_blue=3, total_purple=3
        )

        proxy.update_synthesize()

        # 先用蓝：4个蓝→1个紫，还需2个紫
        # 再用绿：18个绿→2个紫
        assert proxy.synthesize.purple == 3
        assert proxy.synthesize.blue == 0
        assert proxy.synthesize.green == 0

    def test_partial_blue_synthesis(self, mock_item):
        """测试部分蓝合成的情况"""
        # 有5个溢出的蓝，需要1个紫（只用3个蓝）
        proxy = self.create_proxy(
            mock_item,
            value_green=0, value_blue=8, value_purple=0,
            total_green=0, total_blue=3, total_purple=1
        )

        proxy.update_synthesize()

        # 5个蓝只用3个合成1个紫
        assert proxy.synthesize.purple == 1
        assert proxy.synthesize.blue == 0
        assert proxy.synthesize.green == 0

    def test_item_without_group_base(self):
        """测试没有group_base的item"""
        item = Broken_Teeth_of_Iron_Wolf

        proxy = StoredPlannerProxy(
            item=item,
            value=100,
            total=50,
            synthesize=0
        )

        proxy.update_synthesize()

        # 没有group_base的item，synthesize应该为0
        assert proxy.synthesize == 0


class TestMultiValue:
    """测试MultiValue类的基本功能"""

    def test_multivalue_creation(self):
        """测试MultiValue创建"""
        mv = MultiValue(green=10, blue=5, purple=2)
        assert mv.green == 10
        assert mv.blue == 5
        assert mv.purple == 2

    def test_multivalue_default(self):
        """测试MultiValue默认值"""
        mv = MultiValue()
        assert mv.green == 0
        assert mv.blue == 0
        assert mv.purple == 0

    def test_multivalue_add(self):
        """测试MultiValue加法"""
        mv1 = MultiValue(green=10, blue=5, purple=2)
        mv2 = MultiValue(green=5, blue=3, purple=1)
        mv1.add(mv2)
        assert mv1.green == 15
        assert mv1.blue == 8
        assert mv1.purple == 3

    def test_multivalue_subtract(self):
        """测试MultiValue减法"""
        mv1 = MultiValue(green=10, blue=5, purple=2)
        mv2 = MultiValue(green=5, blue=3, purple=1)
        result = mv1 - mv2
        assert result.green == 5
        assert result.blue == 2
        assert result.purple == 1

    def test_multivalue_subtract_negative(self):
        """测试MultiValue减法不会产生负数"""
        mv1 = MultiValue(green=5, blue=3, purple=1)
        mv2 = MultiValue(green=10, blue=8, purple=5)
        result = mv1 - mv2
        assert result.green == 0
        assert result.blue == 0
        assert result.purple == 0

    def test_equivalent_green(self):
        """测试等价绿材料计算"""
        mv = MultiValue(green=10, blue=5, purple=2)
        # 10 + 5*3 + 2*9 = 10 + 15 + 18 = 43
        assert mv.equivalent_green() == 43

    def test_clear(self):
        """测试清空操作"""
        mv = MultiValue(green=10, blue=5, purple=2)
        mv.clear()
        assert mv.green == 0
        assert mv.blue == 0
        assert mv.purple == 0


class TestEdgeCases:
    """测试边界情况"""

    @pytest.fixture
    def mock_item(self):
        return Worldbreaker_Blade

    def test_zero_overflow(self, mock_item):
        """测试溢出为0的情况"""
        proxy = StoredPlannerProxy(
            item=mock_item,
            value=MultiValue(green=10, blue=5, purple=2),
            total=MultiValue(green=10, blue=5, purple=2),
            synthesize=MultiValue()
        )

        proxy.update_synthesize()

        assert proxy.synthesize.purple == 0
        assert proxy.synthesize.blue == 0
        assert proxy.synthesize.green == 0

    def test_one_material_type_only(self, mock_item):
        """测试只有一种材料类型溢出"""
        proxy = StoredPlannerProxy(
            item=mock_item,
            value=MultiValue(green=100, blue=0, purple=0),
            total=MultiValue(green=10, blue=0, purple=5),
            synthesize=MultiValue()
        )

        proxy.update_synthesize()

        # 90个绿可以合成10个紫，但只需要5个
        assert proxy.synthesize.purple == 5
        assert proxy.synthesize.blue == 0
        assert proxy.synthesize.green == 0

    def test_mixed_with_insufficient_green(self, mock_item):
        """测试混合模式但绿不足的情况"""
        # 有2个溢出的蓝（不足3个），6个溢出的绿（不足9个），需要1个紫
        proxy = StoredPlannerProxy(
            item=mock_item,
            value=MultiValue(green=8, blue=4, purple=0),
            total=MultiValue(green=2, blue=2, purple=1),
            synthesize=MultiValue()
        )

        proxy.update_synthesize()

        # 2个蓝不够，但2蓝+6绿(2个蓝)=4个蓝，可以合成1个紫
        assert proxy.synthesize.purple == 1
        assert proxy.synthesize.blue == 0
        assert proxy.synthesize.green == 0
