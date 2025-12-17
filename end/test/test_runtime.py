"""
运行时环境测试模块
测试 RuntimeEnvironment 类
"""
import unittest
from ..src.dsl.runtime import RuntimeEnvironment


class TestRuntimeEnvironment(unittest.TestCase):
    """测试运行时环境"""

    def setUp(self):
        """测试前置设置"""
        self.runtime = RuntimeEnvironment()

    def test_set_and_get_variable(self):
        """测试变量设置和获取"""
        # 测试带$前缀的变量名
        self.runtime.set_variable("$name", "Alice")
        self.assertEqual(self.runtime.get_variable("$name"), "Alice")

        # 测试不带$前缀的变量名
        self.runtime.set_variable("age", 25)
        self.assertEqual(self.runtime.get_variable("age"), 25)
        self.assertEqual(self.runtime.get_variable("$age"), 25)

    def test_get_nonexistent_variable(self):
        """测试获取不存在的变量"""
        value = self.runtime.get_variable("nonexistent")
        self.assertIsNone(value)

        # 测试默认值
        value = self.runtime.get_variable("nonexistent", "default")
        self.assertEqual(value, "default")

    def test_register_and_jump_label(self):
        """测试标签注册和跳转"""
        self.runtime.register_label("main_loop", 10)
        self.assertTrue(self.runtime.jump_to_label("main_loop"))
        self.assertEqual(self.runtime.current_line, 10)

    def test_jump_to_nonexistent_label(self):
        """测试跳转到不存在的标签"""
        result = self.runtime.jump_to_label("nonexistent")
        self.assertFalse(result)

    def test_set_and_get_reply(self):
        """测试回复消息设置和获取"""
        self.runtime.set_reply("Hello World")
        reply = self.runtime.get_reply()

        self.assertEqual(reply, "Hello World")
        # 获取后应该被清空
        self.assertIsNone(self.runtime.last_reply)

    def test_reset(self):
        """测试重置运行时环境"""
        # 设置一些状态
        self.runtime.set_variable("$name", "Alice")
        self.runtime.register_label("test", 5)
        self.runtime.current_line = 10
        self.runtime.should_exit = True
        self.runtime.set_reply("Hello")

        # 重置
        self.runtime.reset()

        # 验证状态被重置
        self.assertEqual(len(self.runtime.variables), 0)
        self.assertEqual(len(self.runtime.labels), 0)
        self.assertEqual(self.runtime.current_line, 0)
        self.assertFalse(self.runtime.should_exit)
        self.assertIsNone(self.runtime.last_reply)

    def test_defined_intents(self):
        """测试意图定义存储"""
        intents = ["查询商品", "客服咨询", "退出系统"]

        self.runtime.set_defined_intents(intents)
        retrieved = self.runtime.get_defined_intents()

        self.assertEqual(retrieved, intents)
        # 返回的应该是副本
        retrieved.append("新意图")
        self.assertEqual(len(self.runtime.defined_intents), 3)

    def test_current_script_reference(self):
        """测试当前脚本引用"""
        mock_script = {"name": "test_script"}
        self.runtime.set_current_script(mock_script)

        self.assertEqual(self.runtime.current_script, mock_script)

    def test_multiple_variables(self):
        """测试多个变量操作"""
        variables = {
            "$name": "Alice",
            "$age": 25,
            "$city": "Beijing",
            "counter": 1
        }

        for name, value in variables.items():
            self.runtime.set_variable(name, value)

        for name, expected in variables.items():
            actual = self.runtime.get_variable(name)
            self.assertEqual(actual, expected)

        self.assertEqual(len(self.runtime.variables), 4)

    def test_variable_overwrite(self):
        """测试变量覆盖"""
        self.runtime.set_variable("$counter", 1)
        self.runtime.set_variable("$counter", 2)

        self.assertEqual(self.runtime.get_variable("$counter"), 2)
        self.assertEqual(len(self.runtime.variables), 1)

    def test_label_overwrite(self):
        """测试标签覆盖"""
        self.runtime.register_label("main", 5)
        self.runtime.register_label("main", 10)  # 覆盖

        self.assertEqual(self.runtime.labels["main"], 10)

    def test_should_exit_flag(self):
        """测试退出标志"""
        self.assertFalse(self.runtime.should_exit)

        self.runtime.should_exit = True
        self.assertTrue(self.runtime.should_exit)

    def test_current_line_increment(self):
        """测试当前行递增"""
        self.assertEqual(self.runtime.current_line, 0)

        self.runtime.current_line = 5
        self.assertEqual(self.runtime.current_line, 5)

        self.runtime.current_line += 1
        self.assertEqual(self.runtime.current_line, 6)


if __name__ == '__main__':
    unittest.main()