"""Streamlit 界面自动化测试（AppTest）。

通过 Streamlit 官方测试工具 AppTest 在内存中运行 app.py，
验证：初始引导、示例数据加载、指标展示、状态筛选、搜索、异常展示。
文件上传（file_uploader）和下载按钮的人工点击无法在 AppTest 中完整模拟，
属于必须由用户在浏览器中完成的人工验收项目。
"""

from pathlib import Path

import pytest

from streamlit.testing.v1 import AppTest

import src.report_generator as rg

# app.py 位于项目根目录；AppTest.from_file 的相对路径是按调用方文件解析的，
# 因此这里用绝对路径，避免因测试所在目录不同而找不到脚本。
APP_PATH = Path(__file__).resolve().parent.parent / "app.py"


@pytest.fixture
def at(tmp_path, monkeypatch):
    """构造 AppTest 实例，并把报告输出重定向到临时目录。"""
    monkeypatch.setattr(rg, "OUTPUT_DIR", tmp_path)
    return AppTest.from_file(str(APP_PATH))


def test_initial_guidance(at):
    """未加载数据时应显示引导提示，且不报错。"""
    at.run()
    assert not at.exception
    assert len(at.warning) >= 1


def test_sample_data_loads_metrics(at):
    """点击「加载示例数据」后，首页应展示正确的关键指标。"""
    at.run()
    at.button[0].click().run()
    assert not at.exception

    # 首页 5 个指标：商品总数、充足、临界、不足、异常
    values = [m.value for m in at.metric]
    assert values == ["8", "2", "1", "3", "2"]


def test_analysis_status_filter(at):
    """库存分析页按状态筛选应只显示对应状态的商品。"""
    at.run()
    at.button[0].click().run()

    at.radio[0].set_value("📊 库存分析").run()
    at.selectbox[0].set_value("库存不足").run()
    assert not at.exception
    assert len(at.dataframe[0].value) == 3  # 示例数据中 3 件库存不足


def test_analysis_search(at):
    """库存分析页按名称搜索应只显示匹配的商品。"""
    at.run()
    at.button[0].click().run()

    at.radio[0].set_value("📊 库存分析").run()
    at.text_input[0].set_value("鼠标").run()
    assert not at.exception
    assert len(at.dataframe[0].value) == 1  # 只有「无线鼠标」匹配


def test_anomaly_page(at):
    """异常处理页应展示 2 条异常记录。"""
    at.run()
    at.button[0].click().run()

    at.radio[0].set_value("⚠️ 异常处理").run()
    assert not at.exception
    assert len(at.dataframe[0].value) == 2


def test_replenishment_page(at):
    """补货建议页应展示 4 条建议（3 不足 + 1 临界）。"""
    at.run()
    at.button[0].click().run()

    at.radio[0].set_value("🛒 补货建议").run()
    assert not at.exception
    assert len(at.dataframe[0].value) == 4
