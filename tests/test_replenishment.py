"""智能补货建议模块测试。"""

from config.settings import (
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    PRIORITY_URGENT,
    STATUS_CRITICAL,
    STATUS_INSUFFICIENT,
    STATUS_SUFFICIENT,
)
from src.models import AnalysisResult, InventoryRecord
from src.replenishment import generate_suggestions


def _result(current, safety, status, target=None):
    rec = InventoryRecord(
        row_number=2,
        sku="SKU001",
        name="测试商品",
        current_stock=current,
        safety_stock=safety,
        target_stock=target,
    )
    return AnalysisResult(record=rec, status=status, gap=max(safety - current, 0))


def test_insufficient_with_target():
    """有目标库存时，补货量 = 目标库存 - 当前库存。"""
    results = [_result(5, 10, STATUS_INSUFFICIENT, target=20)]
    s = generate_suggestions(results)[0]
    assert s.suggested_quantity == 15.0


def test_insufficient_without_target():
    """无目标库存时，不应编造补货量。"""
    results = [_result(5, 10, STATUS_INSUFFICIENT, target=None)]
    s = generate_suggestions(results)[0]
    assert s.suggested_quantity is None


def test_urgent_when_out_of_stock():
    """当前库存为 0 时，优先级应为急需补货。"""
    results = [_result(0, 5, STATUS_INSUFFICIENT, target=10)]
    s = generate_suggestions(results)[0]
    assert s.priority == PRIORITY_URGENT


def test_critical_priority_low():
    """临界库存商品优先级为低。"""
    results = [_result(10, 10, STATUS_CRITICAL, target=20)]
    s = generate_suggestions(results)[0]
    assert s.priority == PRIORITY_LOW


def test_sufficient_excluded():
    """库存充足商品不应进入补货清单。"""
    results = [_result(18, 10, STATUS_SUFFICIENT)]
    assert generate_suggestions(results) == []


def test_medium_priority():
    """缺口比例较小时，优先级为中。"""
    results = [_result(8, 10, STATUS_INSUFFICIENT, target=15)]
    s = generate_suggestions(results)[0]
    assert s.priority == PRIORITY_MEDIUM
