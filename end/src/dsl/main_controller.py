from typing import Dict, List, Optional

# 导入DSL模块
from lexer import Lexer
from parser import Parser
from runtime import RuntimeEnvironment
from better_interpreter import Interpreter
from nodes import ScriptNode

# 导入LLM模块（使用前面实现的）
from ai_client import IntentClassifier


class DSLController:
    """DSL脚本主控制器"""

    def __init__(self, script_path: str, llm_api_key: Optional[str] = None):
        """
        初始化主控制器

        Args:
            script_path: DSL脚本文件路径
            llm_api_key: DeepSeek API密钥
        """
        self.script_path = script_path
        self.llm_api_key = llm_api_key

        # 初始化组件
        self.script_ast: Optional[ScriptNode] = None
        self.runtime = RuntimeEnvironment()
        self.interpreter = Interpreter(self.runtime)
        self.llm_classifier: Optional[IntentClassifier] = None

        # 对话历史
        self.conversation_history: List[Dict] = []

        # 从DSL脚本解析的意图列表
        self.dsl_intents: List[str] = []

        # 临时存储解析出的标签和意图
        self.parsed_labels: List[str] = []
        self.parsed_intents: List[str] = []

    def initialize(self):
        """初始化系统"""
        print("🚀 正在初始化DSL聊天机器人系统...")

        try:
            # 1. 首先提取DSL中的意图和标签
            print(f"📄 解析脚本: {self.script_path}")
            self._extract_dsl_info()

            # 2. 加载并解析DSL脚本
            self._load_and_parse_script()

            # 3. 初始化LLM模块
            print("🤖 初始化LLM意图识别模块...")
            self._initialize_llm_module()

            # 4. 注册外部函数
            print("🔧 注册外部函数...")
            self._register_external_functions()

            # 5. 设置初始变量
            print("⚙️ 设置初始变量...")
            self._set_initial_variables()

            print("✅ 系统初始化完成！")
            print(f"📋 DSL意图列表: {self.dsl_intents}")
            print("-" * 50)

        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            raise

    def _extract_dsl_info(self):
        """从DSL脚本中提取意图和标签信息"""
        try:
            with open(self.script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()

            # 提取意图定义
            import re

            # 查找intents定义
            intent_pattern = r'intents\s*\{([^}]+)\}'
            intent_match = re.search(intent_pattern, script_content)

            if intent_match:
                intent_str = intent_match.group(1)
                # 提取引号内的意图名称
                intents = re.findall(r'"([^"]+)"', intent_str)
                self.parsed_intents = intents
                print(f"📋 从DSL解析到的意图: {intents}")

            # 查找labels定义
            label_pattern = r'labels\s*\{([^}]+)\}'
            label_match = re.search(label_pattern, script_content)

            if label_match:
                label_str = label_match.group(1)
                # 提取标签名称（去掉冒号）
                labels = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*):?', label_str)
                self.parsed_labels = labels
                print(f"🏷️  从DSL解析到的标签: {labels}")

            # 如果没有明确的intents定义，则查找if语句中的意图
            if not self.parsed_intents:
                self._extract_intents_from_if_statements(script_content)

        except Exception as e:
            print(f"⚠️ DSL信息提取失败: {e}")

    def _extract_intents_from_if_statements(self, script_content: str):
        """从if语句中提取意图名称"""
        try:
            # 查找所有if $intent == "xxx" then的语句
            if_pattern = r'if\s*\$intent\s*==\s*"([^"]+)"\s*then'
            if_matches = re.findall(if_pattern, script_content)

            if if_matches:
                self.parsed_intents = list(set(if_matches))  # 去重
                print(f"📋 从if语句解析到的意图: {self.parsed_intents}")
        except Exception as e:
            print(f"⚠️ 从if语句提取意图失败: {e}")

    def _load_and_parse_script(self):
        """加载并解析DSL脚本"""
        try:
            # 读取脚本文件
            with open(self.script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()

            # 词法分析
            lexer = Lexer(script_content)
            tokens = lexer.tokenize()

            # 语法分析
            parser = Parser(tokens)
            self.script_ast = parser.parse()

            print(f"✅ 脚本解析成功，共 {len(self.script_ast.statements)} 条语句")

        except FileNotFoundError:
            print(f"❌ 脚本文件不存在: {self.script_path}")
            raise
        except Exception as e:
            print(f"❌ 脚本解析错误: {e}")
            raise

    def _initialize_llm_module(self):
        """初始化LLM模块"""
        try:
            # 使用从DSL解析的意图列表
            self.dsl_intents = self.parsed_intents if self.parsed_intents else ["其他"]

            self.llm_classifier = IntentClassifier(api_key=self.llm_api_key)
            print("✅ LLM模块初始化成功")
        except Exception as e:
            print(f"⚠️ LLM模块初始化失败，将使用关键词匹配: {e}")
            self.llm_classifier = None

    def _register_external_functions(self):
        """注册外部函数到解释器"""

        def get_intent_function(user_input: str) -> str:
            """意图识别函数"""
            # 记录用户输入
            self.conversation_history.append({
                'role': 'user',
                'message': user_input,
                'timestamp': self._get_timestamp()
            })

            # 使用LLM识别意图
            if self.llm_classifier:
                try:
                    # 使用DSL中定义的意图列表
                    if not self.dsl_intents:
                        # 如果DSL意图列表为空，使用解析的意图
                        self.dsl_intents = self.parsed_intents if self.parsed_intents else ["其他"]

                    # 调用LLM进行意图识别
                    intent = self.llm_classifier.get_intent(
                        user_input,
                        self.dsl_intents
                    )

                    # 记录识别结果
                    print(f"🤖 LLM识别意图: {intent} (来自DSL意图列表)")
                    return intent

                except Exception as e:
                    print(f"⚠️ LLM识别失败，使用关键词匹配: {e}")

            # 后备方案：基于DSL意图的关键词匹配
            return self._keyword_based_intent(user_input)

        # 注册函数
        self.interpreter.register_function("get_intent", get_intent_function)
        print("✅ 外部函数注册完成")

    def _keyword_based_intent(self, user_input: str) -> str:
        """基于关键词的意图识别（后备方案）"""
        # 创建简化的关键词映射（如果需要）
        keyword_mapping = self._create_keyword_mapping()

        for intent, keywords in keyword_mapping.items():
            if any(keyword in user_input for keyword in keywords):
                print(f"🔍 关键词匹配意图: {intent}")
                return intent

        # 返回DSL中的第一个意图或"其他"
        default_intent = self.dsl_intents[0] if self.dsl_intents else "其他"
        print(f"❓ 未匹配到意图，使用默认: {default_intent}")
        return default_intent

    def _create_keyword_mapping(self) -> Dict[str, List[str]]:
        """根据DSL意图创建关键词映射"""
        # 这里可以根据DSL意图名称自动生成一些关键词
        # 例如，如果意图是"查询商品"，可以生成["商品", "产品", "查看"]等关键词
        mapping = {}

        for intent in self.dsl_intents:
            # 简单的关键词生成逻辑
            keywords = [intent]  # 意图名称本身作为关键词

            # 添加一些常见的中文关键词
            if "查询" in intent:
                keywords.extend(["查找", "搜索", "查", "找"])
            if "商品" in intent:
                keywords.extend(["产品", "物品", "货品"])
            if "客服" in intent:
                keywords.extend(["人工", "帮助", "咨询"])
            if "订单" in intent:
                keywords.extend(["物流", "包裹", "快递"])
            if "退出" in intent:
                keywords.extend(["离开", "结束", "关闭", "退出"])

            mapping[intent] = list(set(keywords))  # 去重

        return mapping

    def _set_initial_variables(self):
        """设置初始变量"""
        # 设置系统变量
        self.runtime.set_variable("$bot_name", "DSL聊天助手")
        self.runtime.set_variable("$welcome_message", "您好！我是聊天助手，请问有什么可以帮助您？")
        self.runtime.set_variable("$user_input", "")
        self.runtime.set_variable("$intent", "")

        # 设置DSL意图列表
        self.runtime.set_variable("$dsl_intents", self.dsl_intents)

        print("✅ 初始变量设置完成")

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def start_interaction(self):
        """开始用户交互"""
        print("\n" + "=" * 60)
        print("🤖 DSL聊天机器人启动成功！")
        print("=" * 60)
        print(f"📋 可识别的意图: {', '.join(self.dsl_intents)}")
        print("输入 '退出' 或 'exit' 结束对话")
        print("-" * 60)

        # 执行初始脚本（显示欢迎消息）
        self._execute_script()

        # 主循环
        while not self.runtime.should_exit:
            try:
                # 获取用户输入
                user_input = input("\n👤 您: ").strip()

                if not user_input:
                    continue

                # 检查退出命令
                if user_input.lower() in ['退出', 'exit', 'quit', 'bye']:
                    print("\n👋 感谢使用，再见！")
                    break

                # 设置用户输入变量
                self.runtime.set_variable("$user_input", user_input)

                # 执行脚本
                replies = self._execute_script()

                # 输出所有回复
                for reply in replies:
                    print(f"🤖 机器人: {reply}")

            except KeyboardInterrupt:
                print("\n\n👋 用户中断，退出系统")
                break
            except Exception as e:
                print(f"❌ 系统错误: {e}")
                print("💡 您可以继续输入或输入'退出'结束对话")

    def _execute_script(self) -> List[str]:
        """执行DSL脚本并返回回复列表"""
        try:
            if not self.script_ast:
                raise ValueError("脚本未初始化")

            # 执行脚本
            # replies = self.interpreter.execute_script(self.script_ast)
            replies = []

            # 重置暂停状态
            self.interpreter.resume_execution()

            # 逐步执行脚本，遇到暂停指令就停止
            while (self.runtime.current_line < len(self.script_ast.statements) and
                   not self.runtime.should_exit):

                # 执行单条指令
                result = self.interpreter.execute_script_step(self.script_ast)

                # 如果有回复，添加到列表
                if result:
                    replies.append(result)

                # 如果执行暂停，停止继续执行
                if self.interpreter.is_execution_paused():
                    pause_reason = self.interpreter.get_pause_reason()
                    print(f"⏸️ 执行暂停，原因: {pause_reason}")
                    break
            # 记录机器人回复
            for reply in replies:
                self.conversation_history.append({
                    'role': 'bot',
                    'message': reply,
                    'timestamp': self._get_timestamp()
                })

            return replies

        except Exception as e:
            print(f"❌ 脚本执行错误: {e}")
            return ["抱歉，系统出现错误，请稍后再试。"]

    def get_conversation_history(self) -> List[Dict]:
        """获取对话历史"""
        return self.conversation_history

    def reset_conversation(self):
        """重置对话"""
        self.conversation_history.clear()
        self.runtime.reset()
        self._set_initial_variables()
        print("🔄 对话已重置")