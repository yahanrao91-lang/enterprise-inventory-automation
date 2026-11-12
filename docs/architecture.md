# 系统架构说明

## 1. 总体架构

本项目采用「分层 + 流程编排」的模块化架构，整体是一条单向数据流水线：

```
Excel 文件
   │
   ▼
excel_reader       数据导入：读取 .xlsx，按表头映射列，跳过空白行
   │
   ▼
data_validator     数据校验：完整性、合法性、重复检查，异常进入异常记录
   │
   ▼
inventory_analyzer 库存分析：充足 / 临界 / 不足 + 库存缺口
   │
   ▼
replenishment      补货建议：补货量、优先级、原因
   │
   ▼
report_generator   报告生成：4 个工作表的 Excel 报告
   │
   ▼
app.py（Streamlit） Web 界面：上传、展示、筛选、下载
```

## 2. 模块职责

| 模块 | 职责 | 关键函数 |
|------|------|---------|
| `config/settings.py` | 集中管理路径、列名映射、业务规则、补货阈值 | 常量 + `ensure_directories()` |
| `src/models.py` | 定义核心数据结构 | `InventoryRecord`、`ValidationIssue`、`AnalysisResult`、`ReplenishmentSuggestion` |
| `src/logger.py` | 统一日志（控制台 + 文件，滚动） | `get_logger(name)` |
| `src/excel_reader.py` | 读取 Excel，处理文件/格式/空文件/缺列/空白行 | `read_inventory(path)` |
| `src/data_validator.py` | 数据校验与异常定位 | `validate(records)` |
| `src/inventory_analyzer.py` | 库存状态分类与缺口计算 | `analyze(records)` |
| `src/replenishment.py` | 补货建议与优先级 | `generate_suggestions(results)` |
| `src/report_generator.py` | 生成带样式的 Excel 报告 | `generate_report(...)` |
| `src/pipeline.py` | 流程编排，串起以上各阶段 | `run_pipeline(path)` |
| `app.py` | Streamlit Web 界面 | — |

## 3. 数据模型

- `InventoryRecord`：一条库存记录，含 Excel 原始行号（`row_number`），用于异常定位。
- `ValidationIssue`：一条异常记录（行号、编号、名称、原因、处理状态）。
- `AnalysisResult`：一个商品的库存状态（充足/临界/不足）和库存缺口。
- `ReplenishmentSuggestion`：一条补货建议（缺口、建议补货量、优先级、原因）。

## 4. 关键设计决策

1. **按表头名称定位列**：`config/settings.py` 维护「Excel 表头 → 字段名」映射，因此列顺序变化、可选列缺失都不影响读取。
2. **业务规则集中管理**：库存状态判断和补货优先级阈值都放在 `settings.py`，修改规则不需要改业务代码。
3. **异常不崩溃**：数据问题进入异常记录列表，而不是抛异常中断整个流程。
4. **不编造补货量**：只有存在「目标库存」时才计算建议补货量；否则提示缺口，建议补货量留空。
5. **报告独立文件**：报告文件名带时间戳，每次运行不覆盖历史报告。

## 5. 技术选型

- **openpyxl**：成熟稳定，纯 Python 读写 xlsx，满足本项目需求。
- **Streamlit**：极简的 Python Web 框架，适合快速构建可演示的数据界面。
- **pandas**：用于界面中的表格展示、筛选和搜索。
- **pytest**：标准测试框架。
- **logging**：标准库，无额外依赖。

不引入数据库、微服务、消息队列等重组件，保证「容易安装、容易运行、容易演示」。
