"""pytest 公共夹具。"""

import pytest
from openpyxl import Workbook


@pytest.fixture
def make_excel(tmp_path):
    """返回一个工厂函数：传入表头和行数据，生成临时 xlsx 文件并返回路径。"""

    def _make(header, rows, filename="test.xlsx"):
        wb = Workbook()
        ws = wb.active
        ws.append(header)
        for row in rows:
            ws.append(row)
        path = tmp_path / filename
        wb.save(path)
        return path

    return _make
