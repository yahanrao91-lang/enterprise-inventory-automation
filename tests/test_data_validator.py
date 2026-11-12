"""数据校验模块测试。"""

from src.data_validator import validate
from src.models import InventoryRecord


def _record(**kwargs):
    defaults = dict(
        row_number=2,
        sku="SKU001",
        name="无线鼠标",
        current_stock=5.0,
        safety_stock=10.0,
        target_stock=None,
        unit_price=None,
    )
    defaults.update(kwargs)
    return InventoryRecord(**defaults)


def test_valid_record_passes():
    """正常记录应通过校验。"""
    result = validate([_record()])
    assert len(result.valid_records) == 1
    assert result.issues == []


def test_empty_name():
    """空商品名称应被标记异常。"""
    result = validate([_record(name=None)])
    assert any("商品名称不能为空" in i.reason for i in result.issues)
    assert result.valid_records == []


def test_missing_current_stock():
    """当前库存缺失应被标记异常。"""
    result = validate([_record(current_stock=None)])
    assert any("当前库存不能为空" in i.reason for i in result.issues)


def test_missing_safety_stock():
    """安全库存缺失应被标记异常。"""
    result = validate([_record(safety_stock=None)])
    assert any("安全库存不能为空" in i.reason for i in result.issues)


def test_stock_as_string():
    """库存字段为字符串应被标记异常。"""
    result = validate([_record(current_stock="abc")])
    assert any("当前库存必须为有效数字" in i.reason for i in result.issues)


def test_negative_stock():
    """库存数量为负数应被标记异常。"""
    result = validate([_record(current_stock=-3.0)])
    assert any("当前库存不能为负数" in i.reason for i in result.issues)


def test_duplicate_sku():
    """商品编号重复应被标记异常。"""
    r1 = _record(row_number=2, sku="SKU001")
    r2 = _record(row_number=3, sku="SKU001", name="机械键盘")
    result = validate([r1, r2])
    assert any("商品编号重复" in i.reason for i in result.issues)


def test_missing_target_stock_is_allowed():
    """目标库存缺失不应报错（由补货建议阶段处理）。"""
    result = validate([_record(target_stock=None)])
    assert result.issues == []
