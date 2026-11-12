"""报告内容深度校验：验证报告里实际写入的数据是否正确。

不只检查文件是否存在、工作表名称是否存在，而是读回 Excel 内容，
核对商品数据、补货数量、异常记录、表头与关键格式是否与输入一致。
"""

from openpyxl import load_workbook

from config.settings import (
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


def _write(tmp_path, monkeypatch, analysis, suggestions, issues):
    import src.report_generator as rg

    monkeypatch.setattr(rg, "OUTPUT_DIR", tmp_path)
    return generate_report(analysis, suggestions, issues)


def _build_full_inputs():
    """构造覆盖不同状态的输入：充足、临界、不足（有/无目标）、异常。"""
    records = [
        InventoryRecord(row_number=2, sku="SKU001", name="无线鼠标",
                        current_stock=5.0, safety_stock=10.0, target_stock=20.0, unit_price=59.9),
        InventoryRecord(row_number=3, sku="SKU002", name="机械键盘",
                        current_stock=18.0, safety_stock=10.0, target_stock=25.0),
        InventoryRecord(row_number=4, sku="SKU003", name="显示器",
                        current_stock=0.0, safety_stock=5.0, target_stock=None),
        InventoryRecord(row_number=5, sku="SKU004", name="键盘膜",
                        current_stock=10.0, safety_stock=10.0, target_stock=20.0),
    ]
    analysis = [
        AnalysisResult(record=records[0], status="库存不足", gap=5.0),
        AnalysisResult(record=records[1], status="库存充足", gap=0.0),
        AnalysisResult(record=records[2], status="库存不足", gap=5.0),
        AnalysisResult(record=records[3], status="临界库存", gap=0.0),
    ]
    suggestions = [
        ReplenishmentSuggestion("SKU001", "无线鼠标", 5.0, 10.0, 20.0, 5.0, 15.0, "高", "库存缺口较大"),
        ReplenishmentSuggestion("SKU003", "显示器", 0.0, 5.0, None, 5.0, None, "急需补货", "商品已经缺货"),
        ReplenishmentSuggestion("SKU004", "键盘膜", 10.0, 10.0, 20.0, 0.0, 10.0, "低", "需要关注"),
    ]
    issues = [
        ValidationIssue(row_number=6, sku="SKU005", name="数据线", reason="当前库存不能为空"),
    ]
    return analysis, suggestions, issues


def test_sheet_names_in_order(tmp_path, monkeypatch):
    """四个工作表名称和顺序应与配置一致。"""
    analysis, suggestions, issues = _build_full_inputs()
    path = _write(tmp_path, monkeypatch, analysis, suggestions, issues)
    wb = load_workbook(path)
    assert wb.sheetnames == [
        SHEET_OVERVIEW, SHEET_DETAIL, SHEET_REPLENISH, SHEET_ANOMALY
    ]


def test_detail_sheet_data(tmp_path, monkeypatch):
    """明细工作表应写入正确的商品数据与库存状态。"""
    analysis, suggestions, issues = _build_full_inputs()
    path = _write(tmp_path, monkeypatch, analysis, suggestions, issues)
    ws = load_workbook(path)[SHEET_DETAIL]

    headers = [c.value for c in ws[1]]
    assert headers == [
        "行号", "商品编号", "商品名称", "当前库存", "安全库存",
        "目标库存", "库存缺口", "库存状态", "商品单价", "商品备注",
    ]

    rows = list(ws.iter_rows(min_row=2, values_only=True))
    assert len(rows) == 4
    # 第 1 条：无线鼠标，库存不足，缺口 5，单价 59.9
    assert rows[0][2] == "无线鼠标"
    assert rows[0][3] == 5.0
    assert rows[0][6] == 5.0
    assert rows[0][7] == "库存不足"
    assert rows[0][8] == 59.9
    # 第 3 条：显示器，无目标库存，目标库存单元格应为空（读回为 None）
    assert rows[2][2] == "显示器"
    assert rows[2][5] is None


def test_replenish_sheet_quantity(tmp_path, monkeypatch):
    """补货建议工作表应写入正确的补货数量与「待配置」提示。"""
    analysis, suggestions, issues = _build_full_inputs()
    path = _write(tmp_path, monkeypatch, analysis, suggestions, issues)
    ws = load_workbook(path)[SHEET_REPLENISH]

    headers = [c.value for c in ws[1]]
    assert headers == [
        "商品编号", "商品名称", "当前库存", "安全库存",
        "目标库存", "库存缺口", "建议补货量", "补货优先级", "补货原因",
    ]

    rows = list(ws.iter_rows(min_row=2, values_only=True))
    assert len(rows) == 3
    # 无线鼠标：有目标，补货量 = 20 - 5 = 15
    assert rows[0][1] == "无线鼠标"
    assert rows[0][6] == 15.0
    # 显示器：无目标库存，不编造数量
    assert rows[1][1] == "显示器"
    assert rows[1][6] == "待配置目标库存"
    # 键盘膜：临界，目标 20，补货量 10
    assert rows[2][1] == "键盘膜"
    assert rows[2][6] == 10.0


def test_anomaly_sheet_data(tmp_path, monkeypatch):
    """异常记录工作表应写入行号、编号、名称、原因和状态。"""
    analysis, suggestions, issues = _build_full_inputs()
    path = _write(tmp_path, monkeypatch, analysis, suggestions, issues)
    ws = load_workbook(path)[SHEET_ANOMALY]

    headers = [c.value for c in ws[1]]
    assert headers == ["行号", "商品编号", "商品名称", "异常原因", "处理状态"]

    rows = list(ws.iter_rows(min_row=2, values_only=True))
    assert len(rows) == 1
    assert rows[0][0] == 6
    assert rows[0][1] == "SKU005"
    assert rows[0][3] == "当前库存不能为空"
    assert rows[0][4] == "已记录异常"


def test_format_freeze_and_autofilter(tmp_path, monkeypatch):
    """明细工作表应具备冻结首行和自动筛选。"""
    analysis, suggestions, issues = _build_full_inputs()
    path = _write(tmp_path, monkeypatch, analysis, suggestions, issues)
    ws = load_workbook(path)[SHEET_DETAIL]
    assert ws.freeze_panes == "A2"
    assert ws.auto_filter.ref is not None


def test_unique_filenames(tmp_path, monkeypatch):
    """重复运行应生成独立报告文件，不覆盖之前的文件。"""
    analysis, suggestions, issues = _build_full_inputs()
    p1 = _write(tmp_path, monkeypatch, analysis, suggestions, issues)
    p2 = _write(tmp_path, monkeypatch, analysis, suggestions, issues)
    assert p1 != p2
    assert p1.exists()
    assert p2.exists()


def test_overview_counts_records_not_issues(tmp_path, monkeypatch):
    """一条异常记录有多个问题时，数据异常数量应按记录数统计。"""
    issues = [
        ValidationIssue(row_number=2, sku="S1", name=None, reason="商品名称不能为空"),
        ValidationIssue(row_number=2, sku="S1", name=None, reason="当前库存不能为空"),
    ]
    path = _write(tmp_path, monkeypatch, [], [], issues)
    ws = load_workbook(path)[SHEET_OVERVIEW]
    metrics = {r[0]: r[1] for r in ws.iter_rows(min_row=5, values_only=True)}
    assert metrics["数据异常数量"] == 1
    assert metrics["商品总数"] == 1


def test_empty_data_summary(tmp_path, monkeypatch):
    """无任何数据时，总览应给出明确提示而不是「库存充足」。"""
    path = _write(tmp_path, monkeypatch, [], [], [])
    ws = load_workbook(path)[SHEET_OVERVIEW]
    metrics = {r[0]: r[1] for r in ws.iter_rows(min_row=5, values_only=True)}
    assert metrics["商品总数"] == 0
    assert "暂无商品数据" in metrics["总体库存情况"]
