"""端到端流程测试：用示例数据跑完整流程。"""

from config.settings import SAMPLE_DIR
from src.pipeline import run_pipeline


def test_end_to_end_on_sample():
    """使用示例数据跑完整流程，验证各阶段结果和报告生成。"""
    sample = SAMPLE_DIR / "商品库存示例数据.xlsx"
    result = run_pipeline(sample, generate_excel_report=True)

    # 8 行数据中：6 行正常、2 行异常（空库存、负库存）
    assert len(result["records"]) == 8
    assert len(result["validation"].issues) == 2
    assert len(result["analysis"]) == 6
    # 补货建议：3 个库存不足 + 1 个临界
    assert len(result["suggestions"]) == 4

    assert result["report_path"] is not None
    assert result["report_path"].exists()
