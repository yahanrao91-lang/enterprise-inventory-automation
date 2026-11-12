"""库存分析模块测试。"""

from config.settings import STATUS_CRITICAL, STATUS_INSUFFICIENT, STATUS_SUFFICIENT
from src.inventory_analyzer import analyze
from src.models import InventoryRecord


def _record(current, safety):
    return InventoryRecord(
        row_number=2, name="测试商品", current_stock=current, safety_stock=safety
    )


def test_sufficient():
    """库存充足商品判断：当前库存 > 安全库存。"""
    results = analyze([_record(18, 10)])
    assert results[0].status == STATUS_SUFFICIENT


def test_critical():
    """临界库存商品判断：当前库存 == 安全库存。"""
    results = analyze([_record(10, 10)])
    assert results[0].status == STATUS_CRITICAL


def test_insufficient():
    """库存不足商品判断：当前库存 < 安全库存。"""
    results = analyze([_record(5, 10)])
    assert results[0].status == STATUS_INSUFFICIENT


def test_gap():
    """库存缺口计算：安全库存 - 当前库存。"""
    results = analyze([_record(5, 10)])
    assert results[0].gap == 5.0


def test_gap_zero_when_sufficient():
    """库存充足时缺口为 0。"""
    results = analyze([_record(18, 10)])
    assert results[0].gap == 0.0
