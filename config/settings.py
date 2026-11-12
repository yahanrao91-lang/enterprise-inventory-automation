"""集中配置文件。

所有文件路径、Excel 列名映射、库存业务规则和补货阈值都在这里统一管理，
避免散落在各个模块中，方便修改和复用。
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# 目录路径
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
SAMPLE_DIR = DATA_DIR / "sample"
ARCHIVE_DIR = DATA_DIR / "archive"
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "app.log"

# ---------------------------------------------------------------------------
# 日志
# ---------------------------------------------------------------------------
LOG_LEVEL = "INFO"

# ---------------------------------------------------------------------------
# Excel 列名映射：Excel 表头 -> 程序内部字段名
# 读取时按表头名称定位列，因此列的顺序可以变化，可选列缺失也能正常处理。
# ---------------------------------------------------------------------------
COLUMN_MAPPING = {
    "商品编号": "sku",
    "商品名称": "name",
    "当前库存": "current_stock",
    "安全库存": "safety_stock",
    "目标库存": "target_stock",
    "商品单价": "unit_price",
    "商品分类": "category",
    "商品单位": "unit",
    "供应商": "supplier",
    "商品备注": "remark",
}

# 必填列：缺少其中任何一列，文件会被判定为无法处理
REQUIRED_COLUMNS = ["商品名称", "当前库存", "安全库存"]

# ---------------------------------------------------------------------------
# 库存状态（业务规则）
# ---------------------------------------------------------------------------
STATUS_SUFFICIENT = "库存充足"    # 当前库存 > 安全库存
STATUS_CRITICAL = "临界库存"      # 当前库存 == 安全库存
STATUS_INSUFFICIENT = "库存不足"  # 当前库存 < 安全库存
STATUS_ABNORMAL = "数据异常"      # 数据校验未通过，无法正常判断

# ---------------------------------------------------------------------------
# 补货优先级（可配置阈值）
# ---------------------------------------------------------------------------
# 当前库存 <= 该值时，判定为"急需补货"（默认：已完全缺货）
REPLENISH_URGENT_THRESHOLD = 0.0
# 库存缺口占安全库存的比例达到该值时，判定为"高"优先级（0-1）
REPLENISH_HIGH_RATIO = 0.5

# 补货优先级文字
PRIORITY_URGENT = "急需补货"
PRIORITY_HIGH = "高"
PRIORITY_MEDIUM = "中"
PRIORITY_LOW = "低"

# ---------------------------------------------------------------------------
# 报告
# ---------------------------------------------------------------------------
REPORT_FILE_PREFIX = "库存分析报告"

# 报告工作表名称
SHEET_OVERVIEW = "库存分析总览"
SHEET_DETAIL = "商品库存明细"
SHEET_REPLENISH = "补货建议"
SHEET_ANOMALY = "数据异常记录"


def ensure_directories() -> None:
    """确保运行所需的目录都存在。"""
    for directory in (INPUT_DIR, OUTPUT_DIR, SAMPLE_DIR, ARCHIVE_DIR, LOG_DIR):
        directory.mkdir(parents=True, exist_ok=True)
