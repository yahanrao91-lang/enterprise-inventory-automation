from pathlib import Path
from openpyxl import load_workbook, Workbook

project_dir = Path(__file__).resolve().parent.parent
excel_path = project_dir / "data" / "input" / "商品库存测试数据.xlsx"

workbook = load_workbook(excel_path, data_only=True)
sheet = workbook.active

count = 0
low_stock_products = []
report_workbook = Workbook()
report_sheet = report_workbook.active
report_sheet.append(["商品编号", "商品名称", "当前库存", "安全库存","商品单价"])

for row in sheet.iter_rows(min_row=2, values_only=True):
    if row[0] is None or row[0] == "":
        print("异常：商品编号缺失")

    elif row[1] is None or row[1] == "":
        print("异常：商品名称缺失")

    elif row[2] is None or row[2] == "" or row[3] is None or row[3] == "":
        print("异常：库存数据缺失")

    else:
        print(row[0], row[1])
        count = count + 1
        if row[2] < row[3]:
            low_stock_products.append(row[1])
            report_sheet.append([row[0], row[1], row[2], row[3], row[4]])

print("商品总数：", count)
print("库存不足的商品：", low_stock_products)

# Save the report workbook
report_workbook.save(project_dir / "data" / "output" / "库存不足商品报告.xlsx")