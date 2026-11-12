"""企业库存管理与智能补货自动化系统 —— Web 界面入口。

使用 Streamlit 构建，提供数据导入、库存分析、补货建议、报告下载和异常处理
等功能。运行方式：`streamlit run app.py`，或双击项目根目录的 run.bat。
"""

from datetime import datetime
from pathlib import Path
import tempfile

import pandas as pd
import streamlit as st

from config.settings import (
    SAMPLE_DIR,
    STATUS_ABNORMAL,
    STATUS_CRITICAL,
    STATUS_INSUFFICIENT,
    STATUS_SUFFICIENT,
)
from src.excel_reader import ExcelReadError
from src.logger import get_logger
from src.pipeline import run_pipeline
from src.replenishment import quantity_label

logger = get_logger("app")

SAMPLE_FILE = SAMPLE_DIR / "商品库存示例数据.xlsx"

# 页面基本设置
st.set_page_config(
    page_title="企业库存管理与智能补货自动化系统",
    page_icon="📦",
    layout="wide",
)

# ---------------------------------------------------------------------------
# 会话状态初始化
# ---------------------------------------------------------------------------
if "result" not in st.session_state:
    st.session_state.result = None
    st.session_state.error = None
    st.session_state.source = None
    st.session_state.run_time = None


def _run(path, source_name: str) -> None:
    """运行完整流程并把结果存入会话状态。"""
    try:
        result = run_pipeline(str(path))
        st.session_state.result = result
        st.session_state.error = None
    except ExcelReadError as exc:
        st.session_state.result = None
        st.session_state.error = str(exc)
    except Exception as exc:  # noqa: BLE001 - 展示给用户的统一异常提示
        logger.exception("系统运行异常")
        st.session_state.result = None
        st.session_state.error = f"系统运行异常：{exc}"
    st.session_state.run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.source = source_name


# ---------------------------------------------------------------------------
# 数据转换辅助函数
# ---------------------------------------------------------------------------
def _analysis_to_df(analysis) -> pd.DataFrame:
    rows = []
    for r in analysis:
        rec = r.record
        rows.append({
            "行号": rec.row_number,
            "商品编号": rec.sku or "",
            "商品名称": rec.name or "",
            "当前库存": rec.current_stock,
            "安全库存": rec.safety_stock,
            "目标库存": rec.target_stock if rec.target_stock is not None else "",
            "库存缺口": r.gap,
            "库存状态": r.status,
            "商品单价": rec.unit_price if rec.unit_price is not None else "",
            "商品备注": rec.remark or "",
        })
    return pd.DataFrame(rows)


def _suggestions_to_df(suggestions) -> pd.DataFrame:
    rows = []
    for s in suggestions:
        rows.append({
            "商品编号": s.sku or "",
            "商品名称": s.name or "",
            "当前库存": s.current_stock,
            "安全库存": s.safety_stock,
            "目标库存": s.target_stock if s.target_stock is not None else "",
            "库存缺口": s.gap,
            "建议补货量": quantity_label(s),
            "补货优先级": s.priority,
            "补货原因": s.reason,
        })
    return pd.DataFrame(rows)


def _issues_to_df(issues) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "行号": i.row_number,
            "商品编号": i.sku or "",
            "商品名称": i.name or "",
            "异常原因": i.reason,
            "处理状态": i.status,
        }
        for i in issues
    ])


def _status_counts(result):
    analysis = result["analysis"]
    # 异常数量按"记录数"统计：一条记录可能有多个问题，不能按问题条数重复计数
    abnormal = len(result["records"]) - len(analysis)
    return {
        "商品总数": len(result["records"]),
        STATUS_SUFFICIENT: sum(1 for r in analysis if r.status == STATUS_SUFFICIENT),
        STATUS_CRITICAL: sum(1 for r in analysis if r.status == STATUS_CRITICAL),
        STATUS_INSUFFICIENT: sum(1 for r in analysis if r.status == STATUS_INSUFFICIENT),
        STATUS_ABNORMAL: abnormal,
    }


# ---------------------------------------------------------------------------
# 侧边栏：数据源 + 导航
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("📦 库存自动化系统")
    st.caption("企业库存管理与智能补货自动化")

    st.subheader("数据源")
    uploaded = st.file_uploader("上传库存 Excel 文件（.xlsx）", type=["xlsx"])

    if uploaded is not None and st.session_state.source != uploaded.name:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(uploaded.getvalue())
            tmp_path = tmp.name
        _run(tmp_path, uploaded.name)

    if st.button("加载示例数据", use_container_width=True):
        if SAMPLE_FILE.exists():
            _run(SAMPLE_FILE, "示例数据")
        else:
            st.session_state.error = f"示例数据文件不存在：{SAMPLE_FILE}"

    if st.session_state.source:
        st.caption(f"当前数据：{st.session_state.source}")

    st.divider()
    page = st.radio(
        "功能导航",
        ["🏠 首页", "📥 数据导入", "📊 库存分析", "🛒 补货建议", "📄 报告", "⚠️ 异常处理"],
    )

# ---------------------------------------------------------------------------
# 主区域
# ---------------------------------------------------------------------------
st.title("企业库存管理与智能补货自动化系统")

result = st.session_state.result

# 错误提示
if st.session_state.error:
    st.error(f"处理失败：{st.session_state.error}")
    st.info("请检查文件后重新上传，或点击左侧「加载示例数据」体验完整流程。")

# 未加载数据时的引导
if result is None:
    st.warning("👈 请先在左侧上传 Excel 文件，或点击「加载示例数据」开始分析。")
    st.stop()

# 有数据后，渲染各页面
counts = _status_counts(result)
analysis_df = _analysis_to_df(result["analysis"])
suggestions_df = _suggestions_to_df(result["suggestions"])
issues_df = _issues_to_df(result["validation"].issues)

if page == "🏠 首页":
    st.subheader("库存管理概览")
    st.caption(f"最近一次运行时间：{st.session_state.run_time}")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("商品总数", counts["商品总数"])
    col2.metric(STATUS_SUFFICIENT, counts[STATUS_SUFFICIENT])
    col3.metric(STATUS_CRITICAL, counts[STATUS_CRITICAL])
    col4.metric(STATUS_INSUFFICIENT, counts[STATUS_INSUFFICIENT])
    col5.metric(STATUS_ABNORMAL, counts[STATUS_ABNORMAL])

    st.divider()
    st.markdown("#### 处理流程")
    st.markdown(
        "Excel 数据导入 → 数据校验 → 库存分析 → 库存状态判断 → "
        "补货需求计算 → 异常记录 → 生成分析报告"
    )
    st.info(
        "提示：使用左侧导航查看「库存分析」「补货建议」「报告」和「异常处理」"
        "的详细内容。"
    )

elif page == "📥 数据导入":
    st.subheader("数据导入")
    st.caption("上传 Excel 文件后，系统会自动读取并校验数据。")

    if SAMPLE_FILE.exists():
        with open(SAMPLE_FILE, "rb") as f:
            st.download_button(
                "下载示例 Excel 文件",
                data=f.read(),
                file_name=SAMPLE_FILE.name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    st.markdown("#### 导入数据预览（前 20 行）")
    st.dataframe(analysis_df.head(20), use_container_width=True, hide_index=True)
    st.caption(
        f"共读取 {len(result['records'])} 行数据，其中正常 {len(result['analysis'])} 行、"
        f"异常 {len(result['validation'].issues)} 行。"
    )

elif page == "📊 库存分析":
    st.subheader("库存分析")
    st.caption("查看所有正常商品的库存信息及判断结果，支持按状态筛选和搜索。")

    col_a, col_b = st.columns(2)
    status_filter = col_a.selectbox(
        "按库存状态筛选",
        ["全部", STATUS_SUFFICIENT, STATUS_CRITICAL, STATUS_INSUFFICIENT],
    )
    keyword = col_b.text_input("搜索商品（按名称或编号）")

    filtered = analysis_df
    if status_filter != "全部":
        filtered = filtered[filtered["库存状态"] == status_filter]
    if keyword.strip():
        kw = keyword.strip()
        filtered = filtered[
            filtered["商品名称"].astype(str).str.contains(kw, case=False, regex=False, na=False)
            | filtered["商品编号"].astype(str).str.contains(kw, case=False, regex=False, na=False)
        ]

    st.dataframe(filtered, use_container_width=True, hide_index=True)

elif page == "🛒 补货建议":
    st.subheader("补货建议")
    st.caption("展示需要补货的商品、补货优先级和有依据的补货数量建议。")

    if suggestions_df.empty:
        st.success("当前没有需要补货的商品，库存整体健康。")
    else:
        st.dataframe(suggestions_df, use_container_width=True, hide_index=True)

        no_target = suggestions_df[suggestions_df["目标库存"] == ""]
        if not no_target.empty:
            st.warning(
                f"有 {len(no_target)} 件商品缺少「目标库存」，建议补货量暂无法计算，"
                "请在 Excel 中补充目标库存列后重新导入。"
            )

elif page == "📄 报告":
    st.subheader("报告")
    st.caption("查看本次分析结果，并下载自动生成的 Excel 分析报告。")

    st.markdown(f"**最近一次运行时间**：{st.session_state.run_time}")

    report_path = result.get("report_path")
    if report_path and Path(report_path).exists():
        with open(report_path, "rb") as f:
            st.download_button(
                "下载 Excel 分析报告",
                data=f.read(),
                file_name=Path(report_path).name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        st.success(f"报告已生成：{Path(report_path).name}")
    else:
        st.warning("本次运行未生成报告。")

    st.markdown("#### 报告包含的工作表")
    st.markdown(
        "- 库存分析总览：商品总数、各状态数量、总体库存情况\n"
        "- 商品库存明细：所有正常商品的库存信息及判断结果\n"
        "- 补货建议：需要补货的商品及补货数量建议\n"
        "- 数据异常记录：数据问题、Excel 行号和具体原因"
    )

elif page == "⚠️ 异常处理":
    st.subheader("异常处理")
    st.caption("展示所有存在数据问题的记录、Excel 行号和具体错误原因。")

    if issues_df.empty:
        st.success("没有发现数据异常，所有记录均通过校验。")
    else:
        st.dataframe(issues_df, use_container_width=True, hide_index=True)
        st.caption(
            "以上异常记录不会进入正常库存分析，请修正数据后重新导入。"
        )
