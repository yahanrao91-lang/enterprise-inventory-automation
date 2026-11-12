"""业务流程编排模块。

把整个库存自动化流程串起来：
读取 Excel → 数据校验 → 库存分析 → 补货建议 → 生成报告。
供 Web 界面和端到端测试复用，避免逻辑重复。
"""

from src.data_validator import validate
from src.excel_reader import read_inventory
from src.inventory_analyzer import analyze
from src.logger import get_logger
from src.replenishment import generate_suggestions
from src.report_generator import generate_report

logger = get_logger("pipeline")


def run_pipeline(excel_path, generate_excel_report: bool = True) -> dict:
    """运行完整库存自动化流程，返回包含各阶段结果的字典。

    返回字典的键：
    - records: 读取到的原始库存记录
    - validation: 数据校验结果（valid_records / issues）
    - analysis: 库存分析结果列表
    - suggestions: 补货建议列表
    - report_path: 生成的报告文件路径（未生成时为 None）
    """
    logger.info("===== 库存自动化流程开始 =====")

    records = read_inventory(excel_path)                    # 1. 数据导入
    validation = validate(records)                          # 2. 数据校验
    analysis = analyze(validation.valid_records)            # 3. 库存分析
    suggestions = generate_suggestions(analysis)            # 4. 补货建议

    report_path = None
    if generate_excel_report:
        report_path = generate_report(                       # 5. 生成报告
            analysis, suggestions, validation.issues
        )

    logger.info("===== 库存自动化流程结束 =====")
    return {
        "records": records,
        "validation": validation,
        "analysis": analysis,
        "suggestions": suggestions,
        "report_path": report_path,
    }
