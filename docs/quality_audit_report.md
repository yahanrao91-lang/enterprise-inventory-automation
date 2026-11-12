# 企业库存自动化项目 —— 独立质量审计与验收报告

> 审计日期：2026-11-08
> 审计方式：逐文件读取实际源码与测试，实证运行，不依赖此前的开发报告。
> 审计范围：全部 Python 源码、测试代码、依赖、Web 界面、示例数据、报告生成、.gitignore、干净环境安装。

---

## 1. 审计范围

| 项目 | 内容 |
|------|------|
| 源码 | `src/` 下 9 个模块、`config/settings.py`、`app.py`、`scripts/create_sample_data.py` |
| 测试 | `tests/` 下 9 个测试文件 |
| 依赖 | `requirements.txt`、`pytest.ini` |
| 界面 | `app.py`（Streamlit 6 页面）、`run.bat` |
| 数据 | `data/sample/商品库存示例数据.xlsx`（8 行）、`data/input/商品库存测试数据.xlsx`（5 行） |
| 报告 | `src/report_generator.py` 生成的 4 工作表 Excel |
| 安全 | `.gitignore`、全项目敏感信息扫描 |
| 环境 | 独立虚拟环境 `.venv_audit` 干净安装 |

### 实际存在的文件与核心模块职责

```
app.py                    # Streamlit 界面：6 页面 + 上传/示例数据/报告下载
run.bat                   # Windows 一键启动（chcp 65001 + streamlit run）
requirements.txt          # openpyxl / streamlit / pandas / pytest
pytest.ini                # pythonpath=. + testpaths=tests
.gitignore
config/settings.py        # 集中配置：路径、列名映射、业务规则、补货阈值、工作表名
src/models.py             # dataclass：记录/异常/校验结果/分析结果/补货建议
src/logger.py             # logging 控制台 + RotatingFileHandler
src/excel_reader.py       # 按表头读列、跳过空白行、中文错误提示
src/data_validator.py     # 非空/数字/非负/编号重复校验，逐条生成异常原因
src/inventory_analyzer.py # 充足/临界/不足分类 + 库存缺口
src/replenishment.py      # 补货量计算 + 优先级 + quantity_label 展示
src/report_generator.py   # 4 工作表报告 + 样式/冻结/筛选 + 唯一文件名
src/pipeline.py           # 编排：读→校验→分析→补货→报告
docs/archive/legacy/read_excel.py    # 早期原型（已归档，保留参考）
docs/archive/legacy/function_test.py # 学习草稿（已归档，保留参考）
scripts/create_sample_data.py  # 生成演示示例数据
tests/                    # 9 个测试文件，49 个用例
docs/                     # 架构、流程、用户手册、演示脚本、简历描述、本报告
```

---

## 2. 项目现有功能核验情况

| 功能 | 状态 | 依据 |
|------|------|------|
| Excel 导入（按表头识别列、跳空白行） | ✅ | 代码 + `test_column_order_changed` 等 |
| 数据校验（空/非数字/负数/编号重复，带行号） | ✅ | 代码 + `test_data_validator.py` |
| 库存分析（充足/临界/不足/异常） | ✅ | 代码 + `test_inventory_analyzer.py` |
| 补货建议（有依据计算、优先级、不编造） | ✅ | 代码 + `test_replenishment.py` + 边界用例 |
| 报告生成（4 工作表、样式、唯一文件名） | ✅ | 代码 + `test_report_content.py` |
| Web 界面（6 页面） | ✅ | AppTest 6 用例 |
| 日志 | ✅ | 运行日志实测输出 |
| 文档 | ✅ | 各文档齐全 |

---

## 3. 业务逻辑测试结果

15 项边界场景逐项核验：

| # | 场景 | 预期 | 实际 | 结论 |
|---|------|------|------|------|
| 1 | 库存 > 安全库存 | 库存充足，不进补货 | 同预期 | ✅ |
| 2 | 库存 = 安全库存 | 临界库存，低优先级 | 同预期 | ✅ |
| 3 | 库存 < 安全库存 | 库存不足，缺口=安全-当前 | 同预期 | ✅ |
| 4 | 库存 = 0 | 不足 + 急需补货 | 同预期 | ✅ |
| 5 | 库存为负数 | 进入异常，不参与分析 | 同预期 | ✅ |
| 6 | 库存字段为空 | 进入异常 | 同预期 | ✅ |
| 7 | 安全库存为空 | 进入异常 | 同预期 | ✅ |
| 8 | 商品名称为空 | 进入异常 | 同预期 | ✅ |
| 9 | 商品编号重复 | 进入异常，定位首次行号 | 同预期 | ✅ |
| 10 | 目标库存缺失 | 允许，补货量不编造 | 同预期 | ✅ |
| 11 | 目标库存 < 当前库存 | 不产生负数补货量 | 修复后：建议量 None + 明确提示 | ✅ |
| 12 | Excel 列顺序变化 | 按表头正确识别 | 同预期 | ✅ |
| 13 | 缺少必要字段 | 中文报错 | 同预期 | ✅ |
| 14 | 只有表头没有数据 | 不崩溃，返回空列表 | 同预期（并修正空数据文案） | ✅ |
| 15 | 完全空白行 | 跳过 | 同预期 | ✅ |

特别检查项：

- **异常记录不进入正常分析**：✅ `pipeline` 只把 `validation.valid_records` 交给分析模块，`test_invalid_records_do_not_enter_analysis` 实证负库存记录被隔离。
- **补货量无负数/错误计算**：✅ 代码中 `suggested_quantity = target - current` 仅在 `target > current` 时执行，恒为正；`test_target_less_than_current_no_negative`、`test_target_equal_current_no_replenish` 覆盖。
- **无目标库存不编造建议**：✅ `suggested_quantity = None`，报告显示「待配置目标库存」。
- **Excel 行号准确**：✅ `enumerate(rows[1:], start=2)` 与空白行跳过逻辑正确；实测原始数据「机械键盘」异常定位为第 3 行。
- **编号/名称重复判断**：✅ 只对「商品编号」查重（合理：编号是唯一标识）；「商品名称」允许重复（同名单品常见），不误报。
- **数据类型处理**：✅ `_to_number` 把数字字符串转 float，非数字字符串原样交给校验模块；`_is_number` 排除 bool，避免 `True` 被当作数字。

---

## 4. 自动化测试结果

```
主环境：49 passed in 3.57s
干净环境：49 passed in 4.05s
```

测试用例分布：

| 文件 | 用例数 | 验证内容 |
|------|-------|----------|
| test_excel_reader.py | 5 | 读取、文件不存在、空文件、缺列、空白行 |
| test_data_validator.py | 8 | 各校验规则、编号重复、目标库存可缺 |
| test_inventory_analyzer.py | 5 | 三态判断、缺口计算 |
| test_replenishment.py | 6 | 补货量、无目标、优先级、排除充足 |
| test_report_generator.py | 2 | 4 工作表存在、总览指标 |
| test_pipeline.py | 1 | 端到端（8 记录→2 异常→6 分析→4 建议） |
| test_edge_cases.py | 8 | 列顺序、可选列、仅表头、多问题记录、异常隔离、目标≤当前 |
| test_report_content.py | 8 | **读回报告内容**核对明细/补货量/异常/表头/格式/唯一文件名 |
| test_app.py | 6 | Streamlit AppTest 界面交互 |

关于「测试是否真的验证业务结果，而不只是检查不报错或文件存在」：

- 原有 `test_report_generator.py` 只检查「文件存在 + 4 个表名存在」，**覆盖不足**。
- 本次新增 `test_report_content.py`，**读回 Excel 内容**逐项核对：
  - 工作表名称与顺序（总览/明细/补货建议/异常记录）
  - 明细表表头 10 列 + 商品数据（名称、库存、缺口、状态、单价、空目标库存）
  - 补货表补货量（15.0 / 待配置目标库存 / 10.0）
  - 异常表行号、编号、原因、状态
  - 冻结窗格 `A2`、自动筛选存在
  - 重复运行生成独立文件（文件名不冲突）

**未删除任何失败测试来换取通过。** 原 27 个用例全部保留，新增 22 个。

---

## 5. Web 交互验证结果

使用 `streamlit.testing.v1.AppTest` 在内存中运行 `app.py`，6 个用例全部通过：

| 验证项 | 结果 |
|--------|------|
| 未加载数据时显示引导提示 | ✅ 无异常，有 warning |
| 加载示例数据后首页指标 | ✅ 商品总数 8 / 充足 2 / 临界 1 / 不足 3 / 异常 2 |
| 库存状态筛选 | ✅ 选「库存不足」后仅显示 3 条 |
| 商品搜索 | ✅ 搜「鼠标」后仅显示 1 条 |
| 异常处理页 | ✅ 显示 2 条异常 |
| 补货建议页 | ✅ 显示 4 条建议 |

**不能仅以「进程能启动」作为通过依据**：以上均验证了实际渲染结果，而非仅启动成功。

---

## 6. 干净环境安装结果

```
python -m venv .venv_audit
.venv_audit/Scripts/python.exe -m pip install -r requirements.txt
```

| 检查项 | 结果 |
|--------|------|
| 依赖完整、无版本冲突 | ✅ 一次安装成功 |
| 安装后版本 | openpyxl 3.1.5 / pandas 3.1.1 / pytest 9.2.0 / streamlit 1.67.0 |
| Python 3.13 正常运行 | ✅ Python 3.13.13 |
| 干净环境跑全部测试 | ✅ 49 passed |
| 干净环境启动 Streamlit | ✅ headless 启动成功（run.bat 底层命令 `python -m streamlit run app.py`） |
| Windows 路径处理 | ✅ pathlib 全项目使用，win32 下测试通过 |
| 中文文件名处理 | ✅ 示例数据为中文文件名，读取/生成均正常 |
| 不影响现有环境 | ✅ 使用独立 `.venv_audit`，主环境未动 |

> `.venv_audit` 为审计用临时环境，已被 `.gitignore` 忽略，验证后可用 `rmdir /s .venv_audit` 删除。

---

## 7. GitHub 安全检查结果

| 检查项 | 结果 |
|--------|------|
| 硬编码密钥/密码/Token | ✅ 全项目扫描无命中 |
| 日志不误提交 | ✅ `logs/`、`*.log` 已忽略 |
| 生成报告不误提交 | ✅ `data/output/*.xlsx` 已忽略 |
| 原始业务数据不误提交 | ✅ **本次修复**：新增 `data/input/` 忽略 |
| 虚拟环境不误提交 | ✅ **本次修复**：`.venv/` 改为 `.venv*/`（覆盖 `.venv_audit`） |
| 保留公开示例数据 | ✅ `data/sample/` 未被忽略 |
| .gitignore 实际生效 | ✅ 在一次性临时 git 仓库中实测：input 数据、venv、输出报告、日志全部被忽略，源码/README/示例数据保留 |

未执行 `git push` 或任何对外发布操作。

---

## 8. 发现的问题

| # | 问题 | 严重度 | 说明 |
|---|------|--------|------|
| 1 | 报告文件名冲突 | 高 | 同一秒两次运行生成同名文件，后者覆盖前者，丢报告 |
| 2 | 异常数量重复计数 | 高 | 一条记录有多个问题时被计为多条异常，首页「商品总数」和报告「数据异常数量」虚高 |
| 3 | 空数据文案误导 | 中 | 只有表头时报告写「库存整体健康，全部商品库存充足」 |
| 4 | 补货量提示不准确 | 中 | 目标库存存在但 ≤ 当前库存时，仍显示「待配置目标库存」，实际目标已配置 |
| 5 | .gitignore 有漏洞 | 高 | `.venv_audit/` 与 `data/input/`（原始业务数据）未被忽略 |

---

## 9. 已修复的问题

| # | 修复方式 | 新增测试 |
|---|---------|---------|
| 1 | `generate_report` 文件名冲突时追加 `_2`、`_3` 序号 | `test_unique_filenames` |
| 2 | 异常数量按「记录数」统计（`len({issue.row_number})`），首页改用 `len(records)` | `test_overview_counts_records_not_issues` |
| 3 | 总览无数据时返回「暂无商品数据，请检查数据文件」 | `test_empty_data_summary` |
| 4 | 新增 `quantity_label()` 区分「待配置目标库存」与「目标库存需大于当前库存」 | `test_quantity_label_variants`、`test_target_less_than_current_no_negative` |
| 5 | `.gitignore` 增加 `data/input/`，`.venv/` 改为 `.venv*/` | 临时 git 仓库实测验证 |

修复后全量测试 49 通过，无回归。

---

## 10. 尚未解决的问题

以下为**非阻断性**的遗留项，均不影响核心流程：

1. **目标库存 ≤ 当前库存** 的业务数据：不产生负数（正确），但系统不额外将其标记为「配置不一致」，仅在补货量列提示「目标库存需大于当前库存」。
2. **一条记录多个问题**：异常明细表按「问题」逐条列出（信息更全），而首页/总览按「记录数」统计——两处口径不同，已在代码注释说明。
3. **原有局限性**（README 已声明）：单机本地、无数据库、仅支持 `.xlsx`、无多用户权限。
4. **早期文件** `docs/archive/legacy/read_excel.py`、`docs/archive/legacy/function_test.py`、`项目进度.md` 为学习阶段产物，非运行代码，已归档保留。

---

## 11. 必须由用户完成的人工验收项目

以下交互无法在自动化测试中完整模拟真实浏览器/系统行为，**未虚构为已完成**，请在实际演示前逐项确认：

1. **浏览器上传 Excel 文件**：在左侧 `file_uploader` 上传一个真实 `.xlsx`，确认能正确解析展示。（底层上传处理与流程已由测试覆盖，但 file_uploader 控件的真实点击无法用 AppTest 模拟。）
2. **浏览器点击「下载 Excel 分析报告」按钮**：确认文件能正常下载并打开。
3. **上传一个错误文件**（如把 `.txt` 改名为 `.xlsx`）：确认页面给出明确中文错误提示，不白屏。
4. **双击 `run.bat`**：确认 Windows 下能自动打开浏览器（其底层命令已 headless 验证启动成功）。
5. **上传前确认 `data/input/` 内没有需要保密的真实数据**（该目录已被 gitignore 忽略，但请自行确认内容）。

---

## 验收结论

**B. 有条件通过。**

主要功能全部完成并通过自动化验证：业务逻辑 15 项边界场景正确，49 个测试在开发环境和干净环境均全部通过，报告内容经读回核对，安全扫描无敏感信息，.gitignore 已补齐并实测生效，干净环境一次安装成功。

审计中发现并修复了 5 个问题（含 2 个高严重度问题：报告文件覆盖、异常数量统计错误），修复后无回归。

**未直接判定 A 的原因**：文件上传、报告下载、错误文件提示、双击 run.bat 这 4 项必须由用户在真实浏览器/Windows 中完成的操作，无法被自动化测试完整覆盖，属于尚未完成的人工验收项。这些不是代码缺陷，而是验证缺口。

**完成第 11 节列出的 5 项人工验收后，即可升级为 A（通过），作为正式求职作品展示。**
