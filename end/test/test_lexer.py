"""
词法分析器测试模块
测试 Lexer 类的 tokenize 方法
"""
import unittest
from ..src.dsl.lexer import Lexer, TokenType


class TestLexer(unittest.TestCase):
    """测试词法分析器"""

    def test_basic_tokens(self):
        """测试基本Token识别"""
        source = 'reply "Hello"'
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        self.assertEqual(len(tokens), 3)
        self.assertEqual(tokens[0].type, TokenType.REPLY)
        self.assertEqual(tokens[1].type, TokenType.STRING)
        self.assertEqual(tokens[1].value, "Hello")

    def test_variable_token(self):
        """测试变量Token"""
        source = '$intent == "查询商品"'
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        self.assertEqual(tokens[0].type, TokenType.VARIABLE)
        self.assertEqual(tokens[0].value, "$intent")
        self.assertEqual(tokens[1].type, TokenType.EQUALS)

    def test_label_token(self):
        """测试标签Token"""
        source = 'main_loop:'
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        self.assertEqual(tokens[0].type, TokenType.LABEL)
        self.assertEqual(tokens[0].value, "main_loop")

    def test_label_with_at(self):
        """测试带@的标签"""
        source = '@process_intent:'
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        self.assertEqual(tokens[0].type, TokenType.AT_SYMBOL)
        self.assertEqual(tokens[1].type, TokenType.LABEL)

    def test_intents_declaration(self):
        """测试意图声明"""
        source = 'intents {"查询商品", "客服咨询"}'
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        self.assertEqual(tokens[0].type, TokenType.INTENTS)
        self.assertEqual(tokens[1].type, TokenType.LBRACE)
        self.assertEqual(tokens[2].type, TokenType.STRING)
        self.assertEqual(tokens[2].value, "查询商品")
        self.assertEqual(tokens[3].type, TokenType.COMMA)

    def test_multiline_script(self):
        """测试多行脚本"""
        source = '''
        reply "Hello"
        if $intent == "query" then goto process:
        '''
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # 统计Token类型
        token_types = [t.type for t in tokens]
        self.assertIn(TokenType.REPLY, token_types)
        self.assertIn(TokenType.IF, token_types)
        self.assertIn(TokenType.GOTO, token_types)

    def test_comment_skipping(self):
        """测试注释跳过"""
        source = '''
        # 这是一条注释
        reply "Hello"  # 行尾注释
        '''
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # 注释应该被跳过，只有REPLY、STRING、EOF
        token_types = [t.type for t in tokens if t.type != TokenType.NEWLINE]
        self.assertEqual(len(token_types), 3)  # REPLY, STRING, EOF

    def test_string_with_spaces(self):
        """测试带空格的字符串"""
        source = 'reply "Hello World"'
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        self.assertEqual(tokens[1].type, TokenType.STRING)
        self.assertEqual(tokens[1].value, "Hello World")

    def test_pause_for_input(self):
        """测试暂停指令"""
        source = 'pause_for_user_input'
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        self.assertEqual(tokens[0].type, TokenType.PAUSE_FOR_INPUT)

    def test_invalid_character(self):
        """测试非法字符"""
        source = 'reply "Hello" %'
        lexer = Lexer(source)

        with self.assertRaises(SyntaxError):
            lexer.tokenize()

    def test_empty_string(self):
        """测试空字符串"""
        source = 'reply ""'
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        self.assertEqual(tokens[1].type, TokenType.STRING)
        self.assertEqual(tokens[1].value, "")


if __name__ == '__main__':
    unittest.main()