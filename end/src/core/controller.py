import os
from typing import List, Optional, Callable
from ..dsl.lexer import Lexer
from ..dsl.parser import Parser
from ..dsl.runtime import RuntimeEnvironment
from ..dsl.interpreter import Interpreter


class DSLController:
    """基础主控系统：协调各个模块的核心控制器"""

    def __init__(self):
        self.runtime = RuntimeEnvironment()
        self.interpreter = Interpreter(self.runtime)
        self.current_script: Optional[ScriptNode] = None

    def load_script_from_file(self, filepath: str):
        """从文件加载DSL脚本"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Script file not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            script_content = f.read()

        return self.load_script_from_string(script_content)

    def load_script_from_string(self, script_content: str):
        """从字符串加载DSL脚本"""
        # 词法分析
        lexer = Lexer(script_content)
        tokens = lexer.tokenize()

        # 语法分析
        parser = Parser(tokens)
        self.current_script = parser.parse()

        print(f"脚本加载成功，共 {len(self.current_script.statements)} 条语句")
        return self.current_script

    def register_external_function(self, name: str, func: Callable):
        """注册外部函数（如LLM意图识别）"""
        self.interpreter.register_function(name, func)

    def execute_script(self) -> List[str]:
        """执行当前加载的脚本"""
        if not self.current_script:
            raise RuntimeError("No script loaded")

        # 重置运行时环境
        self.runtime.reset()

        # 执行脚本
        replies = self.interpreter.execute_script(self.current_script)
        return replies

    def execute_with_input(self, user_input: str) -> List[str]:
        """带用户输入执行脚本（模拟单轮对话）"""
        if not self.current_script:
            raise RuntimeError("No script loaded")

        # 设置用户输入变量
        self.runtime.set_variable("user_input", user_input)

        # 执行脚本
        return self.execute_script()

    def setup_llm_client(self, api_key: str, use_mock: bool = True):
        """设置LLM客户端"""

        if use_mock:
            # 使用模拟客户端（测试阶段）
            from ..llm.yuanbao_client import MockYuanBaoAIClient
            self.llm_client = MockYuanBaoAIClient()
            print("使用模拟LLM客户端（测试模式）")
        else:
            # 使用真实的元宝AI客户端
            from ..llm.yuanbao_client import YuanBaoAIClient
            self.llm_client = YuanBaoAIClient(api_key)
            print("使用真实元宝AI客户端")

        # 将LLM客户端注册到解释器
        def get_intent_function(user_input: str) -> str:
            return self.llm_client.get_intent(user_input)

        self.register_external_function("get_intent", get_intent_function)