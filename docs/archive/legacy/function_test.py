def check_inventory(product_name,stock,safety_stock):
    print(f"商品名称:{product_name}")
    print(f"当前库存:{stock}")
    print(f"安全库存:{safety_stock}")
    if stock < safety_stock:
        print("库存不足，需要补货！")
    else:
        print("库存充足，无需补货。")

check_inventory("机械键盘", 18, 10)
check_inventory("无线鼠标", 5, 10)
check_inventory("显示器", 10, 10)