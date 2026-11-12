"""数据校验与清洗模块。

对读取到的库存记录做完整性、合法性和一致性检查：
- 商品名称不能为空
- 当前库存 / 安全库存不能为空、必须为数字、不能为负数
- 目标库存、商品单价（可选）若填写则必须为数字
- 商品编号不能重复

校验不通过的记录进入异常列表（带 Excel 行号和原因），而不是让整个程序崩溃。
"""

from typing import Any

from src.logger import get_logger
from src.models import InventoryRecord, ValidationIssue, ValidationResult

logger = get_logger("data_validator")


def _is_number(value: Any) -> bool:
    """判断值是否为有效数字（排除 bool）。"""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_blank(value: Any) -> bool:
    """判断值是否为空（None 或空字符串）。"""
    if value is None:
        return True
    return isinstance(value, str) and value.strip() == ""


def validate(records: list[InventoryRecord]) -> ValidationResult:
    """校验库存记录，返回校验结果（通过校验的记录 + 异常记录列表）。"""
    result = ValidationResult()
    seen_sku: dict[str, int] = {}  # 商品编号 -> 首次出现的行号，用于重复检查

    for record in records:
        reasons = _validate_one(record, seen_sku)
        if reasons:
            for reason in reasons:
                result.issues.append(
                    ValidationIssue(
                        row_number=record.row_number,
                        sku=record.sku,
                        name=record.name,
                        reason=reason,
                    )
                )
        else:
            result.valid_records.append(record)

    logger.info(
        "数据校验完成：正常 %d 条，异常 %d 条。",
        len(result.valid_records),
        len(result.issues),
    )
    return result


def _validate_one(record: InventoryRecord, seen_sku: dict[str, int]) -> list[str]:
    """校验单条记录，返回异常原因列表（为空表示通过）。"""
    reasons: list[str] = []

    # 商品名称不能为空
    if _is_blank(record.name):
        reasons.append("商品名称不能为空")

    # 当前库存：非空 + 数字 + 非负
    if _is_blank(record.current_stock):
        reasons.append("当前库存不能为空")
    elif not _is_number(record.current_stock):
        reasons.append("当前库存必须为有效数字")
    elif record.current_stock < 0:
        reasons.append("当前库存不能为负数")

    # 安全库存：非空 + 数字 + 非负
    if _is_blank(record.safety_stock):
        reasons.append("安全库存不能为空")
    elif not _is_number(record.safety_stock):
        reasons.append("安全库存必须为有效数字")
    elif record.safety_stock < 0:
        reasons.append("安全库存不能为负数")

    # 目标库存（可选）：若填写则必须为数字且非负
    if not _is_blank(record.target_stock):
        if not _is_number(record.target_stock):
            reasons.append("目标库存必须为有效数字")
        elif record.target_stock < 0:
            reasons.append("目标库存不能为负数")

    # 商品单价（可选）：若填写则必须为数字
    if not _is_blank(record.unit_price) and not _is_number(record.unit_price):
        reasons.append("商品单价必须为有效数字")

    # 商品编号重复检查（仅在编号非空时检查）
    if not _is_blank(record.sku):
        if record.sku in seen_sku:
            reasons.append(f"商品编号重复（首次出现在第 {seen_sku[record.sku]} 行）")
        else:
            seen_sku[record.sku] = record.row_number

    return reasons
