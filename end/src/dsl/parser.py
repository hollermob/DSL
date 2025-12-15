from typing import List
from lexer import Token, TokenType, Lexer
from nodes import *


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current_token_index = 0
        self.current_token = tokens[0] if tokens else None

    def eat(self, token_type: str) -> Token:
        """消费当前token，并移动到下一个token"""
        if self.current_token.type == token_type:
            token = self.current_token
            self.current_token_index += 1
            if self.current_token_index < len(self.tokens):
                self.current_token = self.tokens[self.current_token_index]
            else:
                self.current_token = None
            return token
        else:
            raise SyntaxError(f"Expected {token_type}, got {self.current_token.type} at line {self.current_token.line}")

    def parse(self) -> ScriptNode:
        """解析整个脚本"""
        statements = []
        # 解析可选的标签声明
        print(self.current_token.line)
        if self.current_token and self.current_token.type == TokenType.LABELS:
            label_decl = self.parse_label_declarations()

            if label_decl:
                statements.append(label_decl)

        while self.current_token and self.current_token.type != TokenType.EOF:
            # 跳过空行
            if self.current_token.type == TokenType.NEWLINE:
                self.eat(TokenType.NEWLINE)
                continue

            statement = self.parse_statement()
            if statement:
                statements.append(statement)

            # 跳过行尾的换行
            if self.current_token and self.current_token.type == TokenType.NEWLINE:
                self.eat(TokenType.NEWLINE)

        return ScriptNode(statements)

    def parse_statement(self) -> ASTNode:
        """解析单条语句"""
        if not self.current_token:
            return None

        if self.current_token.type == TokenType.LABEL:
            return self.parse_label()
        elif self.current_token.type == TokenType.INTENTS:
            return self.parse_intents()
        elif self.current_token.type == TokenType.REPLY:
            return self.parse_reply()
        elif self.current_token.type == TokenType.SET:
            return self.parse_set()
        elif self.current_token.type == TokenType.GET_INTENT:
            return self.parse_get_intent()
        elif self.current_token.type == TokenType.IF:
            return self.parse_if()
        elif self.current_token.type == TokenType.GOTO:
            return self.parse_goto()
        elif self.current_token.type == TokenType.EXIT:
            return self.parse_exit()
        else:
            raise SyntaxError(f"Unexpected token {self.current_token.type} at line {self.current_token.line}")

    def parse_label(self) -> LabelNode:
        """解析标签定义，如: main_loop:"""
        token = self.eat(TokenType.LABEL)
        return LabelNode(token.value)

    def parse_intents(self) -> IntentsNode:
        """解析意图定义语句，如: intents {"greeting", "query_product"}"""
        self.eat(TokenType.INTENTS)
        self.eat(TokenType.LBRACE)

        intent_names = []
        while self.current_token and self.current_token.type == TokenType.STRING:
            # 解析第一个意图
            string_token = self.eat(TokenType.STRING)
            intent_names.append(string_token.value)

            # 如果有逗号，继续解析更多意图
            if self.current_token and self.current_token.type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
            else:
                break

        self.eat(TokenType.RBRACE)
        return IntentsNode(intent_names)

    def parse_reply(self) -> ReplyNode:
        """解析回复语句，如: reply "Hello" """
        self.eat(TokenType.REPLY)
        string_token = self.eat(TokenType.STRING)
        return ReplyNode(string_token.value)

    def parse_set(self) -> SetNode:
        """解析变量赋值，如: set $var = "value" """
        self.eat(TokenType.SET)
        var_token = self.eat(TokenType.VARIABLE)
        self.eat(TokenType.EQUALS)

        # 值可以是字符串或变量
        if self.current_token.type == TokenType.STRING:
            value_token = self.eat(TokenType.STRING)
            value = value_token.value
        elif self.current_token.type == TokenType.VARIABLE:
            value_token = self.eat(TokenType.VARIABLE)
            value = value_token.value
        else:
            raise SyntaxError(f"Expected string or variable after = at line {self.current_token.line}")

        return SetNode(var_token.value, value)

    def parse_get_intent(self) -> GetIntentNode:
        """解析获取意图语句，如: get_intent $user_input"""
        self.eat(TokenType.GET_INTENT)
        var_token = self.eat(TokenType.VARIABLE)
        return GetIntentNode(var_token.value)

    def parse_if(self) -> IfNode:
        """解析条件语句，如: if $intent == "value" then goto label"""
        self.eat(TokenType.IF)
        var_token = self.eat(TokenType.VARIABLE)
        self.eat(TokenType.EQUALS)
        string_token = self.eat(TokenType.STRING)
        self.eat(TokenType.THEN)
        self.eat(TokenType.GOTO)
        label_token = self.eat(TokenType.LABEL)

        return IfNode(var_token.value, string_token.value, label_token.value)

    def parse_goto(self) -> GotoNode:
        """解析跳转语句，如: goto label"""
        self.eat(TokenType.GOTO)
        label_token = self.eat(TokenType.LABEL)
        return GotoNode(label_token.value)

    def parse_exit(self) -> ExitNode:
        """解析退出语句"""
        self.eat(TokenType.EXIT)
        return ExitNode()

    def parse_label_declarations(self) -> LabelDeclarationsNode:
        """解析标签声明语句，如: labels {process_intent, show_products}"""
        self.eat(TokenType.LABELS)
        self.eat(TokenType.LBRACE)

        label_names = []
        while self.current_token and self.current_token.type == TokenType.LABEL:
            # 解析标签名（注意：这里使用LABEL类型，因为label_name和identifier规则相同）
            label_token = self.eat(TokenType.LABEL)
            label_names.append(label_token.value)

            # 如果有逗号，继续解析更多标签
            if self.current_token and self.current_token.type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
            else:
                break
        print(self.current_token.type)
        self.eat(TokenType.RBRACE)
        return LabelDeclarationsNode(label_names)