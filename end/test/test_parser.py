"""
语法分析器测试模块
测试 Parser 类的 parse 方法
"""
import unittest
from unittest.mock import Mock
from src.dsl.lexer import Lexer, TokenType
from src.dsl.parser import Parser
from src.dsl.nodes import *


class TestParser(unittest.TestCase):
    """测试语法分析器"""

    def parse_source(self, source):
        """辅助方法：解析源代码"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        return parser.parse()

    def test_parse_reply(self):
        """测试解析reply语句"""
        source = 'reply "Hello World"'
        script = self.parse_source(source)

        self.assertEqual(len(script.statements), 1)
        self.assertIsInstance(script.statements[0], ReplyNode)
        self.assertEqual(script.statements[0].message, "Hello World")

    def test_parse_label_reference(self):
        """测试解析标签引用（不带@）"""
        source = '''
        process_intent:
        reply "Processing"
        '''
        script = self.parse_source(source)

        self.assertEqual(len(script.statements), 2)
        self.assertIsInstance(script.statements[0], LabelNode)
        self.assertEqual(script.statements[0].name, "process_intent")
        self.assertFalse(script.statements[0].is_definition)


    def test_parse_get_intent(self):
        """测试解析get_intent语句"""
        source = 'get_intent $user_input'
        script = self.parse_source(source)

        self.assertEqual(len(script.statements), 1)
        self.assertIsInstance(script.statements[0], GetIntentNode)
        self.assertEqual(script.statements[0].var_name, "$user_input")

    def test_parse_if_then_goto(self):
        """测试解析if语句"""
        source = 'if $intent == "查询商品" then goto show_products:'
        script = self.parse_source(source)

        self.assertEqual(len(script.statements), 1)
        self.assertIsInstance(script.statements[0], IfNode)
        self.assertEqual(script.statements[0].var_name, "$intent")
        self.assertEqual(script.statements[0].compare_value, "查询商品")
        self.assertEqual(script.statements[0].target_label, "show_products")

    def test_parse_goto(self):
        """测试解析goto语句"""
        source = 'goto main_loop:'
        script = self.parse_source(source)

        self.assertEqual(len(script.statements), 1)
        self.assertIsInstance(script.statements[0], GotoNode)
        self.assertEqual(script.statements[0].target_label, "main_loop")

    def test_parse_exit(self):
        """测试解析exit语句"""
        source = 'exit'
        script = self.parse_source(source)

        self.assertEqual(len(script.statements), 1)
        self.assertIsInstance(script.statements[0], ExitNode)

    def test_parse_intents(self):
        """测试解析intents定义"""
        source = 'intents {"查询商品", "客服咨询", "退出系统"}'
        script = self.parse_source(source)

        self.assertEqual(len(script.statements), 1)
        self.assertIsInstance(script.statements[0], IntentsNode)
        self.assertEqual(script.statements[0].intent_names, ["查询商品", "客服咨询", "退出系统"])

    def test_parse_pause_for_input(self):
        """测试解析pause_for_user_input"""
        source = 'pause_for_user_input'
        script = self.parse_source(source)

        self.assertEqual(len(script.statements), 1)
        self.assertIsInstance(script.statements[0], PauseForInputNode)

    def test_parse_multiple_statements(self):
        """测试解析多个语句"""
        source = '''
        reply "欢迎"
        goto next:
        '''
        script = self.parse_source(source)

        self.assertEqual(len(script.statements), 2)
        self.assertIsInstance(script.statements[0], ReplyNode)
        self.assertIsInstance(script.statements[1], GotoNode)

    def test_parse_with_newlines(self):
        """测试带换行符的解析"""
        source = '''
        reply "Line 1"

        reply "Line 2"

        exit
        '''
        script = self.parse_source(source)

        self.assertEqual(len(script.statements), 3)

    def test_parse_complex_script(self):
        """测试解析复杂脚本"""
        source = '''
        intents {"查询", "退出"}

        start:
            reply "你好"
            pause_for_user_input
            get_intent $user_input

            if $intent == "查询" then goto query:
            if $intent == "退出" then goto exit:

            goto start:

        query:
            reply "正在查询..."
            goto start:

        exit:
            reply "再见"
            exit
        '''

        script = self.parse_source(source)

        # 验证语句数量
        self.assertEqual(len(script.statements), 14)

        # 验证节点类型
        node_types = [type(node) for node in script.statements]
        self.assertIn(IntentsNode, node_types)
        self.assertIn(LabelNode, node_types)
        self.assertIn(ReplyNode, node_types)
        self.assertIn(PauseForInputNode, node_types)
        self.assertIn(GetIntentNode, node_types)
        self.assertIn(IfNode, node_types)
        self.assertIn(GotoNode, node_types)
        self.assertIn(ExitNode, node_types)

    def test_syntax_error(self):
        """测试语法错误"""
        source = 'reply'  # 缺少字符串
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        with self.assertRaises(SyntaxError):
            parser.parse()

    def test_empty_script(self):
        """测试空脚本"""
        source = ''
        script = self.parse_source(source)

        self.assertEqual(len(script.statements), 0)


if __name__ == '__main__':
    unittest.main()