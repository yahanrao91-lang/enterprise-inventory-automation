"""报告生成模块测试。"""

from openpyxl import load_workbook

from config.settings import (
    REPORT_FILE_PREFIX,
    SHEET_ANOMALY,
    SHEET_DETAIL,
    SHEET_OVERVIEW,
    SHEET_REPLENISH,
)
from src.models import (
    AnalysisResult,
    InventoryRecord,
    ReplenishmentSuggestion,
    ValidationIssue,
)
from src.report_generator import generate_report


def _build_inputs():
    rec = InventoryRecord(
        row_number=2,
        sku="SKU001",
        name="无线鼠标",
        current_stock=5.0,
        safety_stock=10.0,
        target_stock=20.0,
        unit_price=59.9,
    )
    analysis = [AnalysisResult(record=rec, status="库存不足", gap=5.0)]
    suggestions = [
        ReplenishmentSuggestion(
            sku="SKU001",
            name="无线鼠标",
            current_stock=5.0,
            safety_stock=10.0,
            target_stock=20.0,
            gap=5.0,
            suggested_quantity=15.0,
            priority="高",
            reason="库存缺口较大",
        )
    ]
    issues = [
        ValidationIssue(row_number=3, sku="SKU009", name="数据线", reason="当前库存不能为空")
    ]
    return analysis, suggestions, issues


def test_report_generated(tmp_path, monkeypatch):
    """Excel 报告应正确生成，包含 4 个工作表。"""
    import src.report_generator as rg

    monkeypatch.setattr(rg, "OUTPUT_DIR", tmp_path)

    analysis, suggestions, issues = _build_inputs()
    path = generate_report(analysis, suggestions, issues)

    assert path.exists()
    assert REPORT_FILE_PREFIX in path.name

    wb = load_workbook(path)
    assert SHEET_OVERVIEW in wb.sheetnames
    assert SHEET_DETAIL in wb.sheetnames
    assert SHEET_REPLENISH in wb.sheetnames
    assert SHEET_ANOMALY in wb.sheetnames


def test_overview_contains_metrics(tmp_path, monkeypatch):
    """总览工作表应包含关键指标。"""
    import src.report_generator as rg

    monkeypatch.setattr(rg, "OUTPUT_DIR", tmp_path)

    analysis, suggestions, issues = _build_inputs()
    path = generate_report(analysis, suggestions, issues)

    ws = load_workbook(path)[SHEET_OVERVIEW]
    values = [cell.value for row in ws.iter_rows() for cell in row]
    assert "商品总数" in values
    assert "库存不足数量" in values
    assert "数据异常数量" in values
