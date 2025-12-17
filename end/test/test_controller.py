"""
主控制器测试模块
测试 DSLController 类的功能
"""
import unittest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from src.dsl.main_controller import DSLController


class TestDSLController(unittest.TestCase):
    """测试主控制器"""

    def setUp(self):
        """测试前置设置"""
        # 创建临时DSL脚本文件
        self.temp_dir = tempfile.mkdtemp()
        self.script_path = os.path.join(self.temp_dir, "test.dsl")

        # 写入测试脚本
        script_content = '''
        intents {"查询商品", "客服咨询", "退出系统"}
        
        @start:
            reply "欢迎使用"
            pause_for_user_input
            get_intent $intent
            
            if $intent == "查询商品" then goto query:
            if $intent == "客服咨询" then goto service:
            if $intent == "退出系统" then goto exit:
            
            goto start:
        
        @query:
            reply "商品列表：..."
            goto start:
        
        @service:
            reply "客服热线：400-123-4567"
            goto start:
        
        @exit:
            reply "再见"
            exit
        '''

        with open(self.script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

    def tearDown(self):
        """测试后清理"""
        # 删除临时文件
        import shutil
        shutil.rmtree(self.temp_dir)

    @patch('main_controller.IntentClassifier')
    def test_initialization(self, mock_intent_classifier):
        """测试初始化"""
        controller = DSLController(self.script_path, "test_api_key")

        self.assertEqual(controller.script_path, self.script_path)
        self.assertEqual(controller.llm_api_key, "test_api_key")
        self.assertIsNotNone(controller.runtime)
        self.assertIsNotNone(controller.interpreter)
        self.assertEqual(controller.conversation_history, [])

    @patch('main_controller.IntentClassifier')
    def test_initialize_success(self, mock_intent_classifier):
        """测试成功初始化"""
        # 模拟LLM分类器
        mock_instance = Mock()
        mock_intent_classifier.return_value = mock_instance

        controller = DSLController(self.script_path, "test_api_key")
        controller.initialize()

        # 验证组件已初始化
        self.assertIsNotNone(controller.script_ast)
        self.assertIsNotNone(controller.llm_classifier)
        self.assertGreater(len(controller.dsl_intents), 0)

    @patch('main_controller.IntentClassifier')
    def test_extract_dsl_info(self, mock_intent_classifier):
        """测试提取DSL信息"""
        controller = DSLController(self.script_path, "test_api_key")
        controller._extract_dsl_info()

        # 验证提取的意图和标签
        self.assertIn("查询商品", controller.parsed_intents)
        self.assertIn("客服咨询", controller.parsed_intents)
        self.assertIn("退出系统", controller.parsed_intents)

        self.assertIn("start", controller.parsed_labels)
        self.assertIn("query", controller.parsed_labels)
        self.assertIn("service", controller.parsed_labels)
        self.assertIn("exit", controller.parsed_labels)

    @patch('main_controller.IntentClassifier')
    def test_initialize_llm_module(self, mock_intent_classifier):
        """测试初始化LLM模块"""
        controller = DSLController(self.script_path, "test_api_key")

        # 先提取意图
        controller._extract_dsl_info()

        # 初始化LLM模块
        controller._initialize_llm_module()

        # 验证意图列表
        expected_intents = ["查询商品", "客服咨询", "退出系统"]
        self.assertEqual(controller.dsl_intents, expected_intents)

        # 验证LLM分类器已创建
        self.assertIsNotNone(controller.llm_classifier)
        mock_intent_classifier.assert_called_once()

    @patch('main_controller.IntentClassifier')
    def test_initialize_llm_module_fallback(self, mock_intent_classifier):
        """测试LLM模块初始化失败时的后备方案"""
        # 模拟初始化失败
        mock_intent_classifier.side_effect = Exception("API错误")

        controller = DSLController(self.script_path, "test_api_key")
        controller._extract_dsl_info()
        controller._initialize_llm_module()

        # 应该使用关键词匹配后备方案
        self.assertIsNone(controller.llm_classifier)
        self.assertEqual(controller.dsl_intents, ["查询商品", "客服咨询", "退出系统"])

    @patch('main_controller.IntentClassifier')
    def test_register_external_functions(self, mock_intent_classifier):
        """测试注册外部函数"""
        controller = DSLController(self.script_path, "test_api_key")
        controller._extract_dsl_info()
        controller._initialize_llm_module()
        controller._load_and_parse_script()

        # 注册外部函数
        controller._register_external_functions()

        # 验证函数已注册
        self.assertIn("get_intent", controller.interpreter.external_functions)

    @patch('main_controller.IntentClassifier')
    def test_keyword_based_intent(self, mock_intent_classifier):
        """测试基于关键词的意图识别"""
        controller = DSLController(self.script_path, "test_api_key")
        controller._extract_dsl_info()
        controller.dsl_intents = ["查询商品", "客服咨询", "退出系统", "其他"]

        # 测试关键词匹配
        intent1 = controller._keyword_based_intent("我想查看商品")
        intent2 = controller._keyword_based_intent("需要人工客服")
        intent3 = controller._keyword_based_intent("退出程序")
        intent4 = controller._keyword_based_intent("无关内容")

        # 验证识别结果
        self.assertEqual(intent1, "查询商品")
        self.assertEqual(intent2, "客服咨询")
        self.assertEqual(intent3, "退出系统")
        self.assertEqual(intent4, "查询商品")  # 默认返回第一个意图

    @patch('main_controller.IntentClassifier')
    def test_create_keyword_mapping(self, mock_intent_classifier):
        """测试创建关键词映射"""
        controller = DSLController(self.script_path, "test_api_key")
        controller.dsl_intents = ["查询商品", "客服咨询", "退出系统"]

        mapping = controller._create_keyword_mapping()

        # 验证映射包含所有意图
        self.assertIn("查询商品", mapping)
        self.assertIn("客服咨询", mapping)
        self.assertIn("退出系统", mapping)

        # 验证关键词扩展
        self.assertIn("商品", mapping["查询商品"])
        self.assertIn("产品", mapping["查询商品"])
        self.assertIn("人工", mapping["客服咨询"])
        self.assertIn("帮助", mapping["客服咨询"])
        self.assertIn("离开", mapping["退出系统"])
        self.assertIn("结束", mapping["退出系统"])

    @patch('main_controller.IntentClassifier')
    def test_set_initial_variables(self, mock_intent_classifier):
        """测试设置初始变量"""
        controller = DSLController(self.script_path, "test_api_key")
        controller._extract_dsl_info()
        controller._initialize_llm_module()

        controller._set_initial_variables()

        # 验证变量已设置
        self.assertEqual(controller.runtime.get_variable("$bot_name"), "DSL聊天助手")
        self.assertEqual(controller.runtime.get_variable("$welcome_message"),
                         "您好！我是聊天助手，请问有什么可以帮助您？")
        self.assertEqual(controller.runtime.get_variable("$dsl_intents"),
                         controller.dsl_intents)

    @patch('main_controller.IntentClassifier')
    @patch('builtins.input', side_effect=["我想查询商品", "退出"])
    @patch('builtins.print')
    def test_start_interaction_cli(self, mock_print, mock_input, mock_intent_classifier):
        """测试命令行交互（模拟）"""
        controller = DSLController(self.script_path, "test_api_key")

        # 模拟LLM意图识别
        mock_llm = Mock()
        mock_llm.get_intent.return_value = "查询商品"
        controller.llm_classifier = mock_llm

        # 初始化
        controller.initialize()

        # 设置应该退出的标志，避免无限循环
        controller.runtime.should_exit = True

        # 启动交互（由于有退出标志，会立即退出）
        controller.start_interaction()

        # 验证至少有一些输出
        self.assertTrue(mock_print.called)

    @patch('main_controller.IntentClassifier')
    def test_execute_script(self, mock_intent_classifier):
        """测试执行脚本"""
        controller = DSLController(self.script_path, "test_api_key")
        controller.initialize()

        # 设置用户输入和意图
        controller.runtime.set_variable("$user_input", "查询商品")
        controller.runtime.set_variable("$intent", "查询商品")

        # 执行脚本
        replies = controller._execute_script()

        # 应该得到一些回复
        self.assertIsInstance(replies, list)

        # 验证对话历史被记录
        self.assertGreater(len(controller.conversation_history), 0)

    @patch('main_controller.IntentClassifier')
    def test_get_conversation_history(self, mock_intent_classifier):
        """测试获取对话历史"""
        controller = DSLController(self.script_path, "test_api_key")
        controller.initialize()

        # 添加一些历史记录
        controller.conversation_history = [
            {'role': 'user', 'message': '你好', 'timestamp': '2024-01-01 10:00:00'},
            {'role': 'bot', 'message': '欢迎', 'timestamp': '2024-01-01 10:00:01'}
        ]

        history = controller.get_conversation_history()

        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]['role'], 'user')
        self.assertEqual(history[1]['role'], 'bot')

    @patch('main_controller.IntentClassifier')
    def test_reset_conversation(self, mock_intent_classifier):
        """测试重置对话"""
        controller = DSLController(self.script_path, "test_api_key")
        controller.initialize()

        # 添加一些状态
        controller.conversation_history.append({'role': 'user', 'message': '测试'})
        controller.runtime.set_variable("$test", "value")
        controller.runtime.current_line = 5
        controller.runtime.should_exit = True

        # 重置对话
        controller.reset_conversation()

        # 验证状态已重置
        self.assertEqual(len(controller.conversation_history), 0)
        self.assertEqual(controller.runtime.current_line, 0)
        self.assertFalse(controller.runtime.should_exit)
        # 初始变量应该被重新设置
        self.assertEqual(controller.runtime.get_variable("$bot_name"), "DSL聊天助手")

    @patch('main_controller.IntentClassifier')
    def test_script_not_found(self, mock_intent_classifier):
        """测试脚本文件不存在的情况"""
        non_existent_path = "/nonexistent/path/script.dsl"
        controller = DSLController(non_existent_path, "test_api_key")

        with self.assertRaises(FileNotFoundError):
            controller.initialize()

    @patch('main_controller.IntentClassifier')
    @patch('builtins.open', side_effect=Exception("读取错误"))
    def test_script_parse_error(self, mock_open, mock_intent_classifier):
        """测试脚本解析错误"""
        controller = DSLController(self.script_path, "test_api_key")

        with self.assertRaises(Exception):
            controller._load_and_parse_script()


if __name__ == '__main__':
    unittest.main()