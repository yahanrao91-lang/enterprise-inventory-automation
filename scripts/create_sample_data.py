"""生成示例库存数据（演示用）。

运行方式：python scripts/create_sample_data.py
生成文件：data/sample/商品库存示例数据.xlsx

示例数据覆盖了所有库存状态，便于现场演示：
- 库存充足（当前库存 > 安全库存）
- 临界库存（当前库存 == 安全库存）
- 库存不足（当前库存 < 安全库存，含目标库存可计算补货量）
- 急需补货（当前库存 == 0）
- 数据异常（当前库存为空 / 为负数）
"""

from pathlib import Path

from openpyxl import Workbook

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DIR = PROJECT_ROOT / "data" / "sample"
SAMPLE_FILE = SAMPLE_DIR / "商品库存示例数据.xlsx"

# 表头
HEADERS = [
    "商品编号", "商品名称", "当前库存", "安全库存", "目标库存",
    "商品单价", "商品分类", "商品单位", "供应商", "商品备注",
]

# 数据行（当前库存为空用 None 表示；负数用于演示异常）
ROWS = [
    ["SKU001", "无线鼠标", 5, 10, 20, 59.9, "电脑外设", "个", "供应商A", "库存不足"],
    ["SKU002", "机械键盘", 18, 10, 25, 199, "电脑外设", "个", "供应商A", "库存充足"],
    ["SKU003", "显示器", 0, 5, 10, 899, "电脑外设", "台", "供应商B", "已缺货"],
    ["SKU004", "USB扩展坞", 8, 10, 15, 79.9, "电脑外设", "个", "供应商A", "库存不足"],
    ["SKU005", "笔记本支架", 30, 10, 40, 49.9, "电脑外设", "个", "供应商C", "库存充足"],
    ["SKU006", "键盘膜", 10, 10, 20, 19.9, "电脑外设", "个", "供应商C", "临界库存"],
    ["SKU007", "数据线", None, 10, 20, 29.9, "电脑外设", "条", "供应商B", "当前库存为空"],
    ["SKU008", "电源适配器", -3, 5, 10, 129, "电脑外设", "个", "供应商B", "库存为负数"],
]


def main() -> None:
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    ws = wb.active
    ws.title = "库存数据"
    ws.append(HEADERS)
    for row in ROWS:
        ws.append(row)

    wb.save(SAMPLE_FILE)
    print(f"示例数据已生成：{SAMPLE_FILE}")


if __name__ == "__main__":
    main()
