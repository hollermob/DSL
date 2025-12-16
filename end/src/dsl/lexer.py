import re
from typing import List, Optional


# 定义Token类型
class TokenType:
    REPLY = "REPLY"
    SET = "SET"
    GET_INTENT = "GET_INTENT"
    IF = "IF"
    THEN = "THEN"
    GOTO = "GOTO"
    EXIT = "EXIT"
    EQUALS = "EQUALS"
    STRING = "STRING"
    VARIABLE = "VARIABLE"
    LABEL = "LABEL"
    LABELS = "LABELS"
    COLON = "COLON"
    NEWLINE = "NEWLINE"
    EOF = "EOF"
    INTENTS = "INTENTS"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    COMMA = "COMMA"
    PAUSE_FOR_INPUT = "PAUSE_FOR_INPUT"

class Token:
    def __init__(self, type: str, value: str, line: int, column: int):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self) -> str:
        return f"Token({self.type}, '{self.value}', line {self.line})"


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []

        # Token正则规则
        self.token_specs = [
            (TokenType.INTENTS, r'intents'),
            (TokenType.LABELS, r'labels'),
            (TokenType.REPLY, r'reply'),
            (TokenType.SET, r'set'),
            (TokenType.GET_INTENT, r'get_intent'),
            (TokenType.PAUSE_FOR_INPUT, r'pause_for_user_input'),
            (TokenType.IF, r'if'),
            (TokenType.THEN, r'then'),
            (TokenType.GOTO, r'goto'),
            (TokenType.EQUALS, r'=='),
            (TokenType.LBRACE, r'\{'),
            (TokenType.RBRACE, r'\}'),
            (TokenType.COMMA, r','),
            (TokenType.STRING, r'\"[^\"]*\"'),
            (TokenType.VARIABLE, r'\$[a-zA-Z_][a-zA-Z0-9_]*'),
            (TokenType.LABEL, r'[a-zA-Z_][a-zA-Z0-9_]*:'),
            (TokenType.COLON, r':'),
            (TokenType.NEWLINE, r'\n'),
            (TokenType.EXIT, r'exit'),
            ('SKIP', r'[ \t]+'),
            ('COMMENT', r'#.*'),
        ]

        # 编译正则表达式
        self.regex_pattern = '|'.join(
            f'(?P<{name}>{pattern})' for name, pattern in self.token_specs if name not in ['SKIP', 'COMMENT'])
        self.pattern = re.compile(self.regex_pattern)

    def tokenize(self) -> List[Token]:
        """将源代码转换为token列表"""
        self.tokens = []
        self.position = 0
        self.line = 1

        while self.position < len(self.source):
            # 跳过空白字符和注释
            if self.source[self.position] in ' \t':
                self.position += 1
                continue
            if self.source[self.position] == '#':
                # 跳过注释直到行尾
                while self.position < len(self.source) and self.source[self.position] != '\n':
                    self.position += 1
                continue

            # 使用正则匹配
            match = self.pattern.match(self.source, self.position)
            if match:
                token_type = match.lastgroup
                token_value = match.group()

                if token_type == TokenType.STRING:
                    # 去掉字符串的引号
                    token_value = token_value[1:-1]
                elif token_type == TokenType.LABEL:
                    # 去掉标签的冒号
                    token_value = token_value[:-1]
                # 创建Token并添加到列表
                token = Token(token_type, token_value, self.line, self.column)
                self.tokens.append(token)

                # 更新位置
                self.position = match.end()
                if token_type == TokenType.NEWLINE:
                    self.line += 1
                    self.column = 1
                else:
                    self.column += len(token_value)
            else:
                # 无法识别的字符
                raise SyntaxError(
                    f"Unknown character at line {self.line}, column {self.column}: '{self.source[self.position]}'")

        # 添加文件结束标记
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens