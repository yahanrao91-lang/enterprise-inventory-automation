"""数据模型：定义项目核心数据结构。

使用 dataclass 统一描述一条库存记录、一条校验异常、一条分析结果和一条补货建议，
让各模块之间传递的数据结构清晰一致。
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class InventoryRecord:
    """一条商品库存记录（从 Excel 读取后的原始数据）。

    row_number 是 Excel 中的真实行号（从表头之后开始），用于异常定位。
    库存类字段在校验通过前可能是数字或字符串，校验后才是 float。
    """

    row_number: int
    sku: Optional[str] = None           # 商品编号
    name: Optional[str] = None          # 商品名称
    current_stock: Any = None           # 当前库存
    safety_stock: Any = None            # 安全库存
    target_stock: Any = None            # 目标库存（可选）
    unit_price: Any = None              # 商品单价（可选）
    category: Optional[str] = None      # 商品分类（可选）
    unit: Optional[str] = None          # 商品单位（可选）
    supplier: Optional[str] = None      # 供应商（可选）
    remark: Optional[str] = None        # 商品备注（可选）


@dataclass
class ValidationIssue:
    """一条数据异常记录。"""

    row_number: int
    sku: Optional[str]
    name: Optional[str]
    reason: str
    status: str = "已记录异常"


@dataclass
class ValidationResult:
    """数据校验结果：包含通过校验的记录和异常记录列表。"""

    valid_records: list[InventoryRecord] = field(default_factory=list)
    issues: list[ValidationIssue] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """一个商品的库存分析结果。"""

    record: InventoryRecord
    status: str   # 库存充足 / 临界库存 / 库存不足
    gap: float    # 库存缺口 = max(安全库存 - 当前库存, 0)


@dataclass
class ReplenishmentSuggestion:
    """一条补货建议。"""

    sku: Optional[str]
    name: Optional[str]
    current_stock: float
    safety_stock: float
    target_stock: Optional[float]
    gap: float
    suggested_quantity: Optional[float]   # 建议补货量；无目标库存时为 None
    priority: str
    reason: str
