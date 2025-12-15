from typing import Dict, Any, Callable, List, Optional
from nodes import *
from runtime import RuntimeEnvironment


class Interpreter:
    """增强的解释器：能够利用运行时环境执行复杂的脚本逻辑"""

    def __init__(self, runtime: RuntimeEnvironment):
        self.runtime = runtime
        # 外部函数注册（用于LLM集成）
        self.external_functions: Dict[str, Callable] = {}
        self._has_jumped = False

    def register_function(self, name: str, func: Callable):
        """注册外部函数"""
        self.external_functions[name] = func

    def execute_script(self, script: ScriptNode) -> List[str]:
        """执行整个脚本，返回所有回复消息"""
        replies = []

        # 第一步：构建标签索引和收集意图定义
        self._build_label_index(script)
        self._collect_intent_definitions(script)


        # 第二步：执行脚本
        self.runtime.current_line = 0
        self.runtime.should_exit = False

        max_iterations = 1000  # 防止无限循环
        iteration_count = 0

        while (self.runtime.current_line < len(script.statements) and
               not self.runtime.should_exit and
               iteration_count < max_iterations):

            node = script.statements[self.runtime.current_line]
            self._execute_node(node)

            # 收集回复消息
            reply = self.runtime.get_reply()
            if reply:
                replies.append(reply)

            # 只有没有发生跳转时，才移动到下一行
            if not self._has_jumped:
                self.runtime.current_line += 1
            else:
                self._has_jumped = False

            iteration_count += 1

        if iteration_count >= max_iterations:
            raise RuntimeError("Possible infinite loop detected")

        return replies

    def _build_label_index(self, script: ScriptNode):
        """构建标签位置索引"""
        self.runtime.labels.clear()
        for line_number, node in enumerate(script.statements):
            if isinstance(node, LabelNode):
                self.runtime.register_label(node.name, line_number)

    def _collect_intent_definitions(self, script: ScriptNode):
        """收集脚本中定义的所有意图"""
        all_intents = []
        for node in script.statements:
            if isinstance(node, IntentsNode):
                all_intents.extend(node.intent_names)

        # 去重并设置到运行时环境
        self.runtime.set_defined_intents(list(set(all_intents)))

    def _execute_node(self, node: ASTNode):
        """执行单个AST节点"""
        self._has_jumped = False

        if isinstance(node, LabelNode):
            # 标签：不执行操作，只是位置标记
            pass

        elif isinstance(node, IntentsNode):
            # 意图定义节点：不执行操作，已经在_collect_intent_definitions中处理
            pass

        elif isinstance(node, GetIntentNode):
            # 获取意图：调用外部函数，并传入定义的意图列表
            if "get_intent" in self.external_functions:
                input_text = self.runtime.get_variable(node.var_name, "")
                defined_intents = self.runtime.get_defined_intents()

                # 将定义的意图列表传递给外部函数
                intent = self.external_functions["get_intent"](input_text, defined_intents)
                self.runtime.set_variable("intent", intent)
            else:
                raise RuntimeError("get_intent function not registered")

        elif isinstance(node, ReplyNode):
            # 回复语句：设置回复消息
            # 处理变量引用（如 "Hello $name"）
            message = self._resolve_variables_in_string(node.message)
            self.runtime.set_reply(message)

        elif isinstance(node, SetNode):
            # 赋值语句
            value = node.value
            # 如果值是变量引用，获取变量的实际值
            if isinstance(value, str) and value.startswith('$'):
                actual_value = self.runtime.get_variable(value)
                if actual_value is None:
                    raise RuntimeError(f"Undefined variable: {value}")
                value = actual_value

            self.runtime.set_variable(node.var_name, value)

        elif isinstance(node, GetIntentNode):
            # 获取意图：调用外部函数
            if "get_intent" in self.external_functions:
                input_text = self.runtime.get_variable(node.var_name, "")
                intent = self.external_functions["get_intent"](input_text)
                # 将识别结果存储到intent变量中
                self.runtime.set_variable("intent", intent)
            else:
                raise RuntimeError("get_intent function not registered")

        elif isinstance(node, IfNode):
            # 条件判断
            var_value = self.runtime.get_variable(node.var_name, "")
            if var_value == node.compare_value:
                success = self.runtime.jump_to_label(node.target_label)
                if success:
                    self._has_jumped = True
                else:
                    raise RuntimeError(f"Label not found: {node.target_label}")

        elif isinstance(node, GotoNode):
            # 无条件跳转
            success = self.runtime.jump_to_label(node.target_label)
            if success:
                self._has_jumped = True
            else:
                raise RuntimeError(f"Label not found: {node.target_label}")

        elif isinstance(node, ExitNode):
            # 退出程序
            self.runtime.should_exit = True

        else:
            raise RuntimeError(f"Unknown node type: {type(node)}")

    def _resolve_variables_in_string(self, text: str) -> str:
        """解析字符串中的变量引用（如 "Hello $name"）"""
        result = text
        # 简单的变量替换：查找 $variable 模式
        import re
        variable_pattern = r'\$[a-zA-Z_][a-zA-Z0-9_]*'

        for match in re.finditer(variable_pattern, text):
            var_name = match.group()
            var_value = self.runtime.get_variable(var_name, "")
            result = result.replace(var_name, str(var_value))

        return result