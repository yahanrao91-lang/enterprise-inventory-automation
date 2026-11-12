"""库存分析模块。

根据集中管理的业务规则，对通过校验的商品做库存状态分类：
- 库存充足：当前库存 > 安全库存
- 临界库存：当前库存 == 安全库存
- 库存不足：当前库存 < 安全库存

并为库存不足/临界的商品计算库存缺口（缺口 = 安全库存 - 当前库存，最小为 0）。
"""

from config.settings import STATUS_CRITICAL, STATUS_INSUFFICIENT, STATUS_SUFFICIENT
from src.logger import get_logger
from src.models import AnalysisResult, InventoryRecord

logger = get_logger("inventory_analyzer")


def analyze(records: list[InventoryRecord]) -> list[AnalysisResult]:
    """对一批通过校验的库存记录做库存状态分析。"""
    results: list[AnalysisResult] = []

    for record in records:
        current = float(record.current_stock)
        safety = float(record.safety_stock)

        if current > safety:
            status = STATUS_SUFFICIENT
        elif current == safety:
            status = STATUS_CRITICAL
        else:
            status = STATUS_INSUFFICIENT

        gap = max(safety - current, 0.0)

        results.append(AnalysisResult(record=record, status=status, gap=gap))

    logger.info("库存分析完成，共 %d 条记录。", len(results))
    return results
