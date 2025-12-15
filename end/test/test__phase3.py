#!/usr/bin/env python3
"""第三阶段测试：测试运行时环境和主控系统"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.controller import DSLController


def create_test_script() -> str:
    """创建一个测试用的商店客服DSL脚本"""
    return '''
# 商店客服测试脚本
start:
    reply "欢迎来到TechShop客服！请输入您的问题。"
    set $user_input = "我想查询商品价格"
    get_intent $user_input

main_logic:
    if $intent == "query_price" then goto handle_price
    if $intent == "add_to_cart" then goto handle_cart
    reply "抱歉，我不明白您的需求。"
    goto end

handle_price:
    reply "请问您想查询哪个商品的价格？"
    set $product = "iPhone 15"
    reply "商品 $product 的价格是6999元。"
    goto end

handle_cart:
    reply "正在为您将商品添加到购物车..."
    set $cart_count = 1
    reply "添加成功！购物车已有 $cart_count 件商品。"
    goto end

end:
    reply "感谢您的咨询，再见！"
    exit
'''


def test_phase_3():
    """测试第三阶段功能"""
    print("=== 测试第三阶段：运行时环境与基础主控 ===\\n")

    # 创建主控制器
    controller = DSLController()

    # 注册模拟的意图识别函数
    def mock_get_intent(text):
        if "价格" in text or "多少钱" in text:
            return "query_price"
        elif "购物车" in text or "加入" in text:
            return "add_to_cart"
        else:
            return "unknown"

    controller.register_external_function("get_intent", mock_get_intent)

    # 加载测试脚本
    test_script = create_test_script()
    controller.load_script_from_string(test_script)

    print("1. 测试完整脚本执行：")
    print("-" * 40)
    replies = controller.execute_script()
    for i, reply in enumerate(replies, 1):
        print(f"回复 {i}: {reply}")

    print("\\n2. 测试带用户输入的执行：")
    print("-" * 40)

    # 测试不同用户输入
    test_inputs = [
        "iPhone 15多少钱？",
        "我要把这个加入购物车",
        "你们什么时候开门？"
    ]

    for user_input in test_inputs:
        print(f"用户: {user_input}")
        replies = controller.execute_with_input(user_input)
        for reply in replies:
            print(f"客服: {reply}")
        print()

    print("=== 第三阶段测试完成 ===")


if __name__ == "__main__":
    test_phase_3()