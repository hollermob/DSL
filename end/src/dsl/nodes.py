from abc import ABC, abstractmethod
from typing import List, Any


# AST节点的基类
class ASTNode(ABC):
    @abstractmethod
    def __repr__(self) -> str:
        pass


# 整个脚本的根节点
class ScriptNode(ASTNode):
    def __init__(self, statements: List[ASTNode]):
        self.statements = statements

    def __repr__(self) -> str:
        return f"Script({len(self.statements)} statements)"


# 标签定义节点，如: main_loop:
class LabelNode(ASTNode):
    def __init__(self, name: str):
        self.name = name

    def __repr__(self) -> str:
        return f"Label({self.name})"


# 回复指令节点，如: reply "Hello"
class ReplyNode(ASTNode):
    def __init__(self, message: str):
        self.message = message

    def __repr__(self) -> str:
        return f"Reply('{self.message}')"


# 设置变量指令节点，如: set $intent = "query_product"
class SetNode(ASTNode):
    def __init__(self, var_name: str, value: Any):
        self.var_name = var_name
        self.value = value

    def __repr__(self) -> str:
        return f"Set({self.var_name} = {self.value})"


# 获取意图指令节点，如: get_intent $user_input
class GetIntentNode(ASTNode):
    def __init__(self, var_name: str):
        self.var_name = var_name

    def __repr__(self) -> str:
        return f"GetIntent({self.var_name})"


# 条件跳转节点，如: if $intent == "add_to_cart" then goto add_item
class IfNode(ASTNode):
    def __init__(self, var_name: str, compare_value: str, target_label: str):
        self.var_name = var_name
        self.compare_value = compare_value
        self.target_label = target_label

    def __repr__(self) -> str:
        return f"If({self.var_name} == '{self.compare_value}' then goto {self.target_label})"


# 无条件跳转节点，如: goto main_loop
class GotoNode(ASTNode):
    def __init__(self, target_label: str):
        self.target_label = target_label

    def __repr__(self) -> str:
        return f"Goto({self.target_label})"


# 退出指令节点
class ExitNode(ASTNode):
    def __repr__(self) -> str:
        return "Exit()"

# 意图定义节点
class IntentsNode(ASTNode):
    def __init__(self, intent_names: List[str]):
        self.intent_names = intent_names

    def __repr__(self) -> str:
        return f"Intents({self.intent_names})"

class LabelDeclarationsNode(ASTNode):
    def __init__(self, label_names: List[str]):
        self.label_names = label_names

    def __repr__(self) -> str:
        return f"LabelDeclarations({self.label_names})"


class PauseForInputNode(ASTNode):
    """暂停等待用户输入节点"""

    def __init__(self):
        super().__init__()

    def __repr__(self):
        return "PauseForInputNode()"