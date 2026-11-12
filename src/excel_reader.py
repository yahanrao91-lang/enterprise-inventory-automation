"""Excel 数据导入模块。

负责把 .xlsx 库存文件读入内存，转换为 InventoryRecord 列表。
读取过程中处理：文件不存在、格式错误、空文件、缺少必填列、空白行等。
按表头名称定位列，因此列顺序可以变化，可选列缺失也能正常处理。
"""

from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from config.settings import COLUMN_MAPPING, REQUIRED_COLUMNS
from src.logger import get_logger
from src.models import InventoryRecord

logger = get_logger("excel_reader")


class ExcelReadError(Exception):
    """Excel 读取失败（文件不存在、格式错误、空文件、缺少必填列等）。"""


def _to_number(value: Any) -> Any:
    """把单元格值尽量转为数字；无法转换时原样返回（交给校验模块标记异常）。"""
    if value is None:
        return None
    if isinstance(value, bool):
        return value  # bool 交给校验模块判为非法
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if text == "":
            return None
        try:
            return float(text)
        except ValueError:
            return value  # 非数字字符串，原样返回，交给校验
    return value


def _to_text(value: Any) -> str | None:
    """把单元格值转为去除首尾空白的字符串；空单元格返回 None。"""
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _get_cell(row: tuple, column_index: dict, field: str) -> Any:
    """按字段名从一行数据中取单元格值。"""
    idx = column_index.get(field)
    if idx is None or idx >= len(row):
        return None
    return row[idx]


def read_inventory(excel_path) -> list[InventoryRecord]:
    """读取库存 Excel 文件，返回库存记录列表。

    参数 excel_path 可以是 str 或 pathlib.Path。
    读取失败时抛出 ExcelReadError，错误信息为中文、便于用户理解。
    """
    path = Path(excel_path)
    logger.info("开始读取 Excel 文件：%s", path)

    if not path.exists():
        raise ExcelReadError(f"文件不存在：{path}")

    # 读取工作簿；格式错误（不是真正的 xlsx）会抛异常
    try:
        workbook = load_workbook(path, data_only=True)
    except Exception as exc:  # noqa: BLE001 - 统一转为中文错误提示
        logger.error("Excel 文件打开失败：%s", exc)
        raise ExcelReadError(
            f"无法读取该文件，请确认它是一个有效的 .xlsx 文件。技术信息：{exc}"
        ) from exc

    sheet = workbook.active
    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        raise ExcelReadError("Excel 文件是空的（没有表头行）。")

    # 解析表头：字段名 -> 列索引
    header = rows[0]
    column_index: dict[str, int] = {}
    for idx, cell in enumerate(header):
        header_text = str(cell).strip() if cell is not None else ""
        field = COLUMN_MAPPING.get(header_text)
        if field:
            column_index[field] = idx

    # 检查必填列
    missing = [
        col for col in REQUIRED_COLUMNS if COLUMN_MAPPING[col] not in column_index
    ]
    if missing:
        raise ExcelReadError(f"缺少必填列：{', '.join(missing)}。请检查 Excel 表头。")

    # 逐行读取数据
    records: list[InventoryRecord] = []
    for excel_row_number, row in enumerate(rows[1:], start=2):
        if _is_blank_row(row):
            logger.debug("跳过空白行：第 %d 行", excel_row_number)
            continue

        records.append(
            InventoryRecord(
                row_number=excel_row_number,
                sku=_to_text(_get_cell(row, column_index, "sku")),
                name=_to_text(_get_cell(row, column_index, "name")),
                current_stock=_to_number(_get_cell(row, column_index, "current_stock")),
                safety_stock=_to_number(_get_cell(row, column_index, "safety_stock")),
                target_stock=_to_number(_get_cell(row, column_index, "target_stock")),
                unit_price=_to_number(_get_cell(row, column_index, "unit_price")),
                category=_to_text(_get_cell(row, column_index, "category")),
                unit=_to_text(_get_cell(row, column_index, "unit")),
                supplier=_to_text(_get_cell(row, column_index, "supplier")),
                remark=_to_text(_get_cell(row, column_index, "remark")),
            )
        )

    logger.info("读取完成，共 %d 条记录（不含表头和空白行）。", len(records))
    return records


def _is_blank_row(row: tuple) -> bool:
    """判断一行是否完全为空。"""
    if row is None:
        return True
    return all(
        cell is None or (isinstance(cell, str) and not cell.strip()) for cell in row
    )
