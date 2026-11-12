"""报告生成模块。

生成格式规范的 Excel 报告，包含 4 个工作表：
1. 库存分析总览（关键指标汇总）
2. 商品库存明细（所有正常商品的库存信息及判断结果）
3. 补货建议（需要补货的商品及有依据的补货数量）
4. 数据异常记录（数据问题、Excel 行号和具体原因）

报告具备：清晰表头、合理列宽、表格样式、冻结窗格、自动筛选、状态标识。
每次运行生成独立文件（文件名带时间戳），避免覆盖之前的结果。
"""

from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from config.settings import (
    OUTPUT_DIR,
    REPORT_FILE_PREFIX,
    SHEET_ANOMALY,
    SHEET_DETAIL,
    SHEET_OVERVIEW,
    SHEET_REPLENISH,
    STATUS_CRITICAL,
    STATUS_INSUFFICIENT,
    STATUS_SUFFICIENT,
)
from src.logger import get_logger
from src.models import AnalysisResult, ReplenishmentSuggestion, ValidationIssue
from src.replenishment import quantity_label

logger = get_logger("report_generator")

# 样式常量
HEADER_FILL = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFF")
TITLE_FONT = Font(bold=True, size=14)
CENTER = Alignment(horizontal="center", vertical="center")

# 库存状态 -> 单元格底色（状态标识）
STATUS_COLOR = {
    STATUS_SUFFICIENT: "C6EFCE",   # 绿色：充足
    STATUS_CRITICAL: "FFEB9C",     # 黄色：临界
    STATUS_INSUFFICIENT: "FFC7CE",  # 红色：不足
}


def generate_report(
    analysis_results: list[AnalysisResult],
    suggestions: list[ReplenishmentSuggestion],
    issues: list[ValidationIssue],
) -> Path:
    """生成库存分析报告，返回生成的文件路径。"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now()
    base = f"{REPORT_FILE_PREFIX}_{generated_at.strftime('%Y%m%d_%H%M%S')}"
    output_path = OUTPUT_DIR / f"{base}.xlsx"

    # 同一秒内多次运行时追加序号，确保每次运行生成独立文件，不覆盖之前的结果
    counter = 2
    while output_path.exists():
        output_path = OUTPUT_DIR / f"{base}_{counter}.xlsx"
        counter += 1

    wb = Workbook()

    _write_overview_sheet(wb, analysis_results, issues, generated_at)
    _write_detail_sheet(wb, analysis_results)
    _write_replenish_sheet(wb, suggestions)
    _write_anomaly_sheet(wb, issues)

    # 默认第一个工作表为活动表
    wb.active = 0

    wb.save(output_path)
    logger.info("报告生成成功：%s", output_path)
    return output_path


# ---------------------------------------------------------------------------
# 各工作表写入
# ---------------------------------------------------------------------------

def _write_overview_sheet(wb: Workbook, analysis_results, issues, generated_at) -> None:
    """工作表一：库存分析总览。"""
    ws = wb.active
    ws.title = SHEET_OVERVIEW

    sufficient = sum(1 for r in analysis_results if r.status == STATUS_SUFFICIENT)
    critical = sum(1 for r in analysis_results if r.status == STATUS_CRITICAL)
    insufficient = sum(1 for r in analysis_results if r.status == STATUS_INSUFFICIENT)
    # 一条异常记录可能同时有多个问题，异常数量应按"记录数"统计，不能按问题条数重复计数
    abnormal = len({issue.row_number for issue in issues})
    total = len(analysis_results) + abnormal

    summary = _overall_summary(insufficient, critical, abnormal, total)

    ws["A1"] = "库存分析总览"
    ws["A1"].font = TITLE_FONT
    ws.merge_cells("A1:B1")

    ws["A2"] = f"生成时间：{generated_at.strftime('%Y-%m-%d %H:%M:%S')}"

    rows = [
        ("商品总数", total),
        ("库存充足数量", sufficient),
        ("临界库存数量", critical),
        ("库存不足数量", insufficient),
        ("数据异常数量", abnormal),
        ("总体库存情况", summary),
    ]

    header_row = 4
    ws.cell(row=header_row, column=1, value="统计指标")
    ws.cell(row=header_row, column=2, value="数值")
    _style_header_cells(ws, header_row, 2)

    for i, (label, value) in enumerate(rows, start=header_row + 1):
        ws.cell(row=i, column=1, value=label)
        ws.cell(row=i, column=2, value=value)
        ws.cell(row=i, column=1).font = Font(bold=True)

    ws.column_dimensions["A"].width = 20
    ws.column_dimensions["B"].width = 46


def _write_detail_sheet(wb: Workbook, analysis_results) -> None:
    """工作表二：商品库存明细。"""
    ws = wb.create_sheet(SHEET_DETAIL)

    headers = [
        "行号", "商品编号", "商品名称", "当前库存", "安全库存",
        "目标库存", "库存缺口", "库存状态", "商品单价", "商品备注",
    ]
    ws.append(headers)
    _style_header_cells(ws, 1, len(headers))

    for r in analysis_results:
        rec = r.record
        ws.append([
            rec.row_number,
            rec.sku or "",
            rec.name or "",
            rec.current_stock,
            rec.safety_stock,
            rec.target_stock if rec.target_stock is not None else "",
            r.gap,
            r.status,
            rec.unit_price if rec.unit_price is not None else "",
            rec.remark or "",
        ])
        # 给库存状态单元格着色
        status_cell = ws.cell(row=ws.max_row, column=8)
        color = STATUS_COLOR.get(r.status)
        if color:
            status_cell.fill = PatternFill(
                start_color=color, end_color=color, fill_type="solid"
            )
        status_cell.alignment = CENTER

    _finalize_data_sheet(ws)


def _write_replenish_sheet(wb: Workbook, suggestions) -> None:
    """工作表三：补货建议。"""
    ws = wb.create_sheet(SHEET_REPLENISH)

    headers = [
        "商品编号", "商品名称", "当前库存", "安全库存",
        "目标库存", "库存缺口", "建议补货量", "补货优先级", "补货原因",
    ]
    ws.append(headers)
    _style_header_cells(ws, 1, len(headers))

    for s in suggestions:
        ws.append([
            s.sku or "",
            s.name or "",
            s.current_stock,
            s.safety_stock,
            s.target_stock if s.target_stock is not None else "",
            s.gap,
            quantity_label(s),
            s.priority,
            s.reason,
        ])

    _finalize_data_sheet(ws)


def _write_anomaly_sheet(wb: Workbook, issues) -> None:
    """工作表四：数据异常记录。"""
    ws = wb.create_sheet(SHEET_ANOMALY)

    headers = ["行号", "商品编号", "商品名称", "异常原因", "处理状态"]
    ws.append(headers)
    _style_header_cells(ws, 1, len(headers))

    for issue in issues:
        ws.append([
            issue.row_number,
            issue.sku or "",
            issue.name or "",
            issue.reason,
            issue.status,
        ])

    _finalize_data_sheet(ws)


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _overall_summary(insufficient: int, critical: int, abnormal: int, total: int) -> str:
    """生成"总体库存情况"的文字总结。"""
    if total == 0:
        return "暂无商品数据，请检查数据文件。"
    if abnormal == 0 and insufficient == 0 and critical == 0:
        return "库存整体健康，全部商品库存充足。"
    parts = []
    if insufficient:
        parts.append(f"{insufficient} 件商品库存不足")
    if critical:
        parts.append(f"{critical} 件商品处于临界状态")
    if abnormal:
        parts.append(f"{abnormal} 条数据异常")
    return "存在 " + "、".join(parts) + "，请及时处理。"


def _style_header_cells(ws, row: int, column_count: int) -> None:
    """设置表头行的样式。"""
    for col in range(1, column_count + 1):
        cell = ws.cell(row=row, column=col)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = CENTER


def _finalize_data_sheet(ws) -> None:
    """数据工作表统一收尾：冻结首行、自动筛选、自动列宽。"""
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    _autofit(ws)


def _display_width(value) -> int:
    """估算单元格内容的显示宽度（中文按 2 个字符宽计算）。"""
    text = "" if value is None else str(value)
    return sum(2 if ord(ch) > 127 else 1 for ch in text)


def _autofit(ws, min_width: int = 8, max_width: int = 42) -> None:
    """根据内容自动设置列宽。"""
    for col_idx, column in enumerate(ws.columns, start=1):
        width = max(_display_width(cell.value) for cell in column) + 2
        ws.column_dimensions[get_column_letter(col_idx)].width = max(
            min_width, min(width, max_width)
        )
