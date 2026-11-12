"""业务边界用例测试：覆盖审计中要求的各类边界场景。

这些用例补充原有测试未覆盖的场景：列顺序变化、可选列缺失、
只有表头没有数据、一条记录多个问题、异常记录不进入分析、
目标库存小于/等于当前库存等。
"""

import pytest

from src.data_validator import validate
from src.excel_reader import read_inventory
from src.models import InventoryRecord
from src.pipeline import run_pipeline
from src.replenishment import generate_suggestions, quantity_label
from src.models import AnalysisResult, ReplenishmentSuggestion

HEADERS = ["商品编号", "商品名称", "当前库存", "安全库存", "目标库存"]


# ---------------------------------------------------------------------------
# 数据导入：列顺序变化 / 可选列缺失 / 只有表头
# ---------------------------------------------------------------------------

def test_column_order_changed(make_excel):
    """列顺序打乱后仍能按表头名称正确读取。"""
    path = make_excel(
        ["安全库存", "商品名称", "商品编号", "目标库存", "当前库存"],
        [["10", "无线鼠标", "SKU001", "20", "5"]],
    )
    records = read_inventory(path)
    assert len(records) == 1
    r = records[0]
    assert r.sku == "SKU001"
    assert r.name == "无线鼠标"
    assert r.current_stock == 5.0
    assert r.safety_stock == 10.0
    assert r.target_stock == 20.0


def test_optional_target_column_missing(make_excel):
    """缺少可选列「目标库存」时应正常读取，target_stock 为 None。"""
    path = make_excel(
        ["商品编号", "商品名称", "当前库存", "安全库存"],
        [["SKU001", "无线鼠标", 5, 10]],
    )
    records = read_inventory(path)
    assert records[0].target_stock is None


def test_header_only_returns_empty(make_excel):
    """只有表头、没有数据行时不应崩溃，返回空列表。"""
    path = make_excel(HEADERS, [])
    records = read_inventory(path)
    assert records == []


# ---------------------------------------------------------------------------
# 数据校验：一条记录多个问题
# ---------------------------------------------------------------------------

def test_multi_issue_record_produces_multiple_issues():
    """一条记录同时有多个问题时，异常列表按问题记录，但不进入正常分析。"""
    rec = InventoryRecord(
        row_number=2, sku="SKU001", name=None, current_stock=None, safety_stock=10.0
    )
    result = validate([rec])
    assert len(result.valid_records) == 0
    reasons = [i.reason for i in result.issues]
    assert "商品名称不能为空" in reasons
    assert "当前库存不能为空" in reasons


# ---------------------------------------------------------------------------
# 流程：异常记录不进入正常库存分析
# ---------------------------------------------------------------------------

def test_invalid_records_do_not_enter_analysis(tmp_path, monkeypatch):
    """负库存记录应进入异常，而不是参与正常库存分析。"""
    from openpyxl import Workbook
    import src.report_generator as rg

    monkeypatch.setattr(rg, "OUTPUT_DIR", tmp_path)

    wb = Workbook()
    ws = wb.active
    ws.append(["商品编号", "商品名称", "当前库存", "安全库存"])
    ws.append(["SKU001", "正常商品", 5, 10])   # 正常（库存不足）
    ws.append(["SKU002", "负库存商品", -3, 5])  # 异常（负数）
    path = tmp_path / "mix.xlsx"
    wb.save(path)

    result = run_pipeline(path)
    assert len(result["records"]) == 2
    assert len(result["analysis"]) == 1           # 只有正常商品进入分析
    assert len(result["validation"].issues) == 1  # 负库存商品进入异常
    assert result["analysis"][0].record.sku == "SKU001"


# ---------------------------------------------------------------------------
# 补货建议：目标库存小于/等于当前库存，不产生负数
# ---------------------------------------------------------------------------

def _result(current, safety, status, target):
    rec = InventoryRecord(
        row_number=2, sku="SKU001", name="测试商品",
        current_stock=current, safety_stock=safety, target_stock=target,
    )
    return AnalysisResult(record=rec, status=status, gap=max(safety - current, 0))


def test_target_less_than_current_no_negative():
    """目标库存小于当前库存时，不产生负数补货量。"""
    results = [_result(8, 10, "库存不足", target=5)]
    s = generate_suggestions(results)[0]
    assert s.suggested_quantity is None


def test_target_equal_current_no_replenish():
    """目标库存等于当前库存时，补货量为 None（无需补货）。"""
    results = [_result(10, 10, "临界库存", target=10)]
    s = generate_suggestions(results)[0]
    assert s.suggested_quantity is None


def test_quantity_label_variants():
    """补货量展示文本：有数量返回数值，无目标/目标不大于当前时给出明确说明。"""
    with_qty = ReplenishmentSuggestion(
        "SKU001", "A", 5.0, 10.0, 20.0, 5.0, 15.0, "高", "缺口大"
    )
    assert quantity_label(with_qty) == 15.0

    no_target = ReplenishmentSuggestion(
        "SKU002", "B", 5.0, 10.0, None, 5.0, None, "中", "低于安全库存"
    )
    assert quantity_label(no_target) == "待配置目标库存"

    target_too_low = ReplenishmentSuggestion(
        "SKU003", "C", 8.0, 10.0, 5.0, 2.0, None, "中", "低于安全库存"
    )
    assert quantity_label(target_too_low) == "目标库存需大于当前库存"
