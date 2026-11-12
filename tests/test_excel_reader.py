"""Excel 数据导入模块测试。"""

import pytest
from openpyxl import Workbook

from src.excel_reader import ExcelReadError, read_inventory

HEADERS = ["商品编号", "商品名称", "当前库存", "安全库存"]


def test_read_normal_data(make_excel):
    """正常库存数据读取。"""
    path = make_excel(
        HEADERS,
        [
            ["SKU001", "无线鼠标", 5, 10],
            ["SKU002", "机械键盘", 18, 10],
        ],
    )
    records = read_inventory(path)

    assert len(records) == 2
    assert records[0].sku == "SKU001"
    assert records[0].name == "无线鼠标"
    assert records[0].current_stock == 5.0
    assert records[0].safety_stock == 10.0
    assert records[0].row_number == 2
    assert records[1].row_number == 3


def test_file_not_exists(tmp_path):
    """文件不存在时的异常处理。"""
    with pytest.raises(ExcelReadError, match="文件不存在"):
        read_inventory(tmp_path / "不存在的文件.xlsx")


def test_empty_file(tmp_path):
    """空 Excel 文件处理。"""
    wb = Workbook()
    path = tmp_path / "empty.xlsx"
    wb.save(path)

    with pytest.raises(ExcelReadError, match="空的"):
        read_inventory(path)


def test_missing_required_column(make_excel):
    """缺少必要字段时应报错。"""
    path = make_excel(
        ["商品编号", "商品名称", "安全库存"],  # 缺少"当前库存"
        [["SKU001", "无线鼠标", 10]],
    )
    with pytest.raises(ExcelReadError, match="缺少必填列"):
        read_inventory(path)


def test_blank_rows_skipped(make_excel):
    """空白行应被跳过。"""
    path = make_excel(
        HEADERS,
        [
            ["SKU001", "无线鼠标", 5, 10],
            [None, None, None, None],  # 空白行
            ["SKU002", "机械键盘", 18, 10],
        ],
    )
    records = read_inventory(path)
    assert len(records) == 2
