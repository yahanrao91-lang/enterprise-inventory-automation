"""智能补货建议模块。

根据库存分析结果生成补货建议：
- 库存充足的商品不进入补货清单
- 临界库存商品标记为"低"优先级（需要关注）
- 库存不足商品计算库存缺口，并按可配置阈值划分优先级
- 建议补货量只有在存在"目标库存"时才计算，否则提示需要配置目标库存
"""

from config.settings import (
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    PRIORITY_URGENT,
    REPLENISH_HIGH_RATIO,
    REPLENISH_URGENT_THRESHOLD,
    STATUS_CRITICAL,
    STATUS_INSUFFICIENT,
    STATUS_SUFFICIENT,
)
from src.logger import get_logger
from src.models import AnalysisResult, ReplenishmentSuggestion

logger = get_logger("replenishment")


def generate_suggestions(
    results: list[AnalysisResult],
) -> list[ReplenishmentSuggestion]:
    """根据分析结果生成补货建议列表（只包含需要关注和需要补货的商品）。"""
    suggestions: list[ReplenishmentSuggestion] = []

    for result in results:
        if result.status == STATUS_SUFFICIENT:
            continue  # 库存充足，不需要补货

        record = result.record
        current = float(record.current_stock)
        safety = float(record.safety_stock)

        target = float(record.target_stock) if record.target_stock is not None else None

        # 建议补货量：有目标库存且目标大于当前库存时才计算
        if target is not None and target > current:
            suggested_quantity = target - current
        else:
            suggested_quantity = None

        priority, reason = _priority_reason(result.status, current, safety)

        suggestions.append(
            ReplenishmentSuggestion(
                sku=record.sku,
                name=record.name,
                current_stock=current,
                safety_stock=safety,
                target_stock=target,
                gap=result.gap,
                suggested_quantity=suggested_quantity,
                priority=priority,
                reason=reason,
            )
        )

    logger.info("补货建议生成完成，共 %d 条。", len(suggestions))
    return suggestions


def quantity_label(suggestion: ReplenishmentSuggestion) -> "str | float":
    """返回补货量的展示值：能计算则返回数值，否则说明原因（不编造数量）。"""
    if suggestion.suggested_quantity is not None:
        return suggestion.suggested_quantity
    if suggestion.target_stock is None:
        return "待配置目标库存"
    return "目标库存需大于当前库存"


def _priority_reason(status: str, current: float, safety: float) -> tuple[str, str]:
    """根据库存状态和可配置阈值判断补货优先级与原因。"""
    if status == STATUS_CRITICAL:
        return PRIORITY_LOW, "当前库存等于安全库存，需要关注"

    # 库存不足
    if current <= REPLENISH_URGENT_THRESHOLD:
        return PRIORITY_URGENT, "商品已经缺货，急需补货"

    gap_ratio = (safety - current) / safety if safety > 0 else 1.0
    if gap_ratio >= REPLENISH_HIGH_RATIO:
        return PRIORITY_HIGH, "库存缺口较大，优先补货"

    return PRIORITY_MEDIUM, "库存低于安全库存，需要补货"
