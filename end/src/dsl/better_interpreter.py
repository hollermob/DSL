from typing import Dict, Any, Callable, Optional
from nodes import *
import runtime


class Interpreter:
    def __init__(self, runtime: runtime.RuntimeEnvironment):
        self.runtime = runtime
        self.external_functions: Dict[str, Callable] = {}
        self._has_jumped = False
        self._label_cache = {}  # 已定义的标签位置
        self._pending_gotos = {}  # 待解析的goto引用：{标签名: [引用位置列表]}
        self._resolved_gotos = set()  # 已解析的goto引用
        self._label_statements_processed = set()  # 已处理的标签语句行号

        self._execution_paused = False  # 是否暂停执行
        self._pause_reason = None  # 暂停原因
        self._pending_replies = []  # 待输出的回复

        self._pause_instructions = {
            "reply",  # 遇到reply应该输出并暂停
            "get_intent"  # 遇到get_intent应该暂停并等待输入
        }


    def register_function(self, name: str, func: Callable):
        """注册外部函数"""
        self.external_functions[name] = func

    def execute_script(self, script: ScriptNode) -> List[str]:
        """执行整个脚本，返回所有回复消息"""
        replies = []
        # 第一阶段：扫描所有标签定义
        self._scan_labels(script)

        # 第二阶段：执行脚本
        self._execute_script_phase2(script, replies)

        return replies

    def _scan_labels(self, script: ScriptNode):
        """第一阶段：扫描并记录所有标签位置"""
        self._label_cache.clear()

        for line_num, node in enumerate(script.statements):
            if isinstance(node, LabelNode):
                self._define_label(node.name, line_num)

    def _execute_script_phase2(self, script: ScriptNode, replies: List[str]):
        """第二阶段：执行脚本"""
        self.runtime.current_line = 0
        self.runtime.should_exit = False
        max_iterations = 1000
        iteration_count = 0

        while (self.runtime.current_line < len(script.statements) and
               not self.runtime.should_exit and
               iteration_count < max_iterations):

            node = script.statements[self.runtime.current_line]
            result = self._execute_node(node, self.runtime.current_line)

            if result and isinstance(result, str):
                replies.append(result)

            if not self._has_jumped:
                self.runtime.current_line += 1
            else:
                self._has_jumped = False

            iteration_count += 1

        if iteration_count >= max_iterations:
            raise RuntimeError("Possible infinite loop detected")

    def _execute_node(self, node: ASTNode, current_line: int) -> Optional[str]:
        """执行单个AST节点，返回回复消息"""
        self._has_jumped = False
        self._execution_paused = False  # 重置暂停状态
        reply_message = None

        if isinstance(node, LabelDeclarationsNode):
            # 预先声明标签：添加到缓存
            for label_name in node.label_names:
                self._predeclare_label(label_name)
        elif isinstance(node, IntentsNode):
            # 处理意图定义节点
            self.runtime.set_defined_intents(node.intent_names)
            print(f"📋 定义意图列表: {node.intent_names}")
        elif isinstance(node, LabelNode):
            # 标签定义：只记录位置，不执行任何操作
            # 检查标签是否已定义，避免重复处理
            if node.name not in self._label_cache or self._label_cache[node.name] == -1:
                self._define_label(node.name, current_line)
            # 标记标签语句已处理
            self._label_statements_processed.add(current_line)
            # 不产生回复，继续执行下一语句

        # elif isinstance(node, ReplyNode):
        #     message = self._resolve_variables_in_string(node.message)
        #     reply_message = message
        #     self.runtime.set_reply(message)
        elif isinstance(node, ReplyNode):
            # 遇到reply指令：立即输出并暂停
            message = self._resolve_variables_in_string(node.message)
            print(f"📤 输出回复: {message}")
            self._execution_paused = True
            self._pause_reason = "reply"
            return message  # 立即返回回复

        elif isinstance(node, SetNode):
            value = node.value
            if isinstance(value, str) and value.startswith('$'):
                actual_value = self.runtime.get_variable(value)
                if actual_value is None:
                    raise RuntimeError(f"未定义变量: {value}")
                value = actual_value
            self.runtime.set_variable(node.var_name, value)
            print(f"🔧 设置变量: {node.var_name} = {value}")

        # elif isinstance(node, GetIntentNode):
        #     if "get_intent" in self.external_functions:
        #         input_text = self.runtime.get_variable(node.var_name, "")
        #         intent = self.external_functions["get_intent"](input_text)
        #         self.runtime.set_variable("intent", intent)
        #         # 清除已处理的标签标记，以便后续跳转能正确执行
        #         self._label_statements_processed.clear()
        #     else:
        #         raise RuntimeError("get_intent函数未注册")
        elif isinstance(node, GetIntentNode):
            # 遇到get_intent指令：暂停并等待外部处理
            print(f"⏸️ 等待意图识别: {node.var_name}")
            self._execution_paused = True
            self._pause_reason = "get_intent"
            return None

        elif isinstance(node, IfNode):
            var_value = self.runtime.get_variable(node.var_name, "")
            print(f"🔍 条件判断: {node.var_name} == '{node.compare_value}'? 当前值: '{var_value}'")
            if var_value == node.compare_value:
                self._jump_to_label(node.target_label, current_line)

        elif isinstance(node, GotoNode):
            print(f"➡️ 跳转到: {node.target_label}")
            self._jump_to_label(node.target_label, current_line)

        elif isinstance(node, ExitNode):
            print("🛑 执行退出指令")
            self.runtime.should_exit = True

        else:
            raise RuntimeError(f"未知节点类型: {type(node)}")

        return reply_message

    def _predeclare_label(self, label_name: str):
        """预先声明标签：标记为已存在但位置未知"""
        print(f"📋 预声明标签: {label_name}")
        # 可以设置一个特殊值表示标签已声明但位置未知
        self._label_cache[label_name] = -1  # 使用-1表示预声明

    def _define_label(self, label_name: str, line_number: int):
        """定义标签：添加到缓存并解析待处理的引用"""
        # 避免重复定义
        if label_name in self._label_cache and self._label_cache[label_name] == line_number:
            return

        print(f"📍 定义标签: {label_name} -> 第{line_number}行")
        self._label_cache[label_name] = line_number

        # 检查是否有待解析的goto引用
        if label_name in self._pending_gotos:
            print(f"🔗 解析待处理的goto引用: {label_name}")
            # 可以在这里重新执行那些goto语句，或者只是记录已解析
            self._resolved_gotos.add(label_name)
            del self._pending_gotos[label_name]

    def _jump_to_label(self, label_name: str, current_line: int):
        """跳转到标签：如果标签已声明直接跳转，否则记录待解析"""
        if label_name in self._label_cache:
            # 标签已声明
            target_line = self._label_cache[label_name]
            if target_line != -1:  # 标签位置已确定
                # 检查目标行是否是标签定义语句
                if target_line in self._label_statements_processed:
                    # 如果目标行是标签定义，跳转到下一行
                    target_line += 1
                    print(f"🔧 调整跳转位置: {label_name} -> 第{target_line}行（跳过标签定义）")

                self.runtime.current_line = target_line
                self._has_jumped = True
                print(f"🔀 跳转到: {label_name} (第{target_line}行)")
            else:
                # 标签已声明但位置未知，记录待解析
                if label_name not in self._pending_gotos:
                    self._pending_gotos[label_name] = []
                self._pending_gotos[label_name].append(current_line)
                print(f"⏳ 等待标签定义: {label_name} (从第{current_line}行引用)")
        else:
            # 标签未声明，报错
            raise RuntimeError(f"未声明的标签: {label_name}")

    def _check_unresolved_labels(self):
        """检查是否有未解析的标签引用"""
        if self._pending_gotos:
            print("❌ 未解析的标签引用:")
            for label_name, references in self._pending_gotos.items():
                print(f"  - {label_name} 被以下行引用: {references}")
            raise RuntimeError(f"存在未定义的标签: {list(self._pending_gotos.keys())}")

    def get_label_status(self):
        """获取标签解析状态（用于调试）"""
        return {
            'defined_labels': list(self._label_cache.keys()),
            'pending_gotos': self._pending_gotos,
            'resolved_gotos': list(self._resolved_gotos)
        }

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

    def execute_script_step(self, script: ScriptNode) -> Optional[str]:
        """单步执行脚本：执行一条指令后返回（如果暂停）"""
        if self.runtime.current_line >= len(script.statements):
            return None

        node = script.statements[self.runtime.current_line]
        result = self._execute_node(node, self.runtime.current_line)

        if not self._has_jumped:
            self.runtime.current_line += 1

        return result

    def is_execution_paused(self) -> bool:
        """检查执行是否暂停"""
        return self._execution_paused

    def get_pause_reason(self) -> Optional[str]:
        """获取暂停原因"""
        return self._pause_reason

    def resume_execution(self):
        """恢复执行"""
        self._execution_paused = False
        self._pause_reason = None