import os
import sys
import threading
import time
from typing import Optional
from pathlib import Path

# 导入DSL控制器和GUI
from src.dsl.main_controller import DSLController
from src.dsl.ui import ChatbotGUI


class DSLApplication:
    """DSL聊天机器人主应用程序"""

    def __init__(self, script_path: str, llm_api_key: Optional[str] = None, timeout_minutes: int = 10):
        """
        初始化应用程序

        Args:
            script_path: DSL脚本文件路径
            llm_api_key: DeepSeek API密钥
            timeout_minutes: 无操作超时时间（分钟）
        """
        self.script_path = script_path
        self.llm_api_key = llm_api_key
        self.timeout_minutes = timeout_minutes

        # 初始化组件
        self.controller: Optional[DSLController] = None
        self.gui: Optional[ChatbotGUI] = None

        # 超时控制
        self.last_activity_time = time.time()
        self.timeout_timer: Optional[threading.Timer] = None
        self.is_running = False

        # 验证脚本文件
        self._validate_script_path()

    def _validate_script_path(self):
        """验证脚本文件路径"""
        if not os.path.exists(self.script_path):
            raise FileNotFoundError(f"DSL脚本文件不存在: {self.script_path}")


    def initialize_components(self):
        """初始化所有组件"""
        print("🚀 正在初始化DSL聊天机器人应用程序...")

        try:
            # 1. 初始化控制器
            self.controller = DSLController(
                script_path=self.script_path,
                llm_api_key=self.llm_api_key
            )
            self.controller.initialize()

            # 2. 初始化GUI（如果需要）
            # 注意：GUI初始化会在单独的线程中进行

            print("✅ 应用程序组件初始化完成")

        except Exception as e:
            print(f"❌ 应用程序初始化失败: {e}")
            raise

    def start_activity_monitor(self):
        """启动活动监控（超时自动退出）"""
        if self.timeout_timer:
            self.timeout_timer.cancel()

        self.last_activity_time = time.time()
        self.timeout_timer = threading.Timer(60.0, self._check_timeout)  # 每分钟检查一次
        self.timeout_timer.daemon = True
        self.timeout_timer.start()

    def _check_timeout(self):
        """检查是否超时"""
        if not self.is_running:
            return

        idle_time = time.time() - self.last_activity_time
        idle_minutes = idle_time / 60

        # 如果超时，自动退出
        if idle_minutes >= self.timeout_minutes:
            print(f"⏰ 检测到{self.timeout_minutes}分钟无操作，自动退出...")
            self.cleanup()
            if self.gui:
                # 在GUI线程中显示退出消息
                self.gui.root.after(0, self._show_timeout_message)
            else:
                print("👋 感谢使用，再见！")
                sys.exit(0)
        else:
            # 继续监控
            remaining_time = self.timeout_minutes - int(idle_minutes)
            if remaining_time <= 3:  # 最后3分钟提醒
                print(f"💡 提示: 系统将在{remaining_time}分钟后因无操作自动退出")

            self.start_activity_monitor()

    def _show_timeout_message(self):
        """在GUI中显示超时消息"""
        if self.gui:
            self.gui.add_message("🤖🤖 系统",
                                 f"检测到{self.timeout_minutes}分钟无操作，系统自动退出。",
                                 is_bot=True)
            self.gui.root.after(2000, self.gui.on_exit)

    def record_user_activity(self):
        """记录用户活动时间"""
        self.last_activity_time = time.time()
        if self.is_running:
            self.start_activity_monitor()

    def run_cli_mode(self):
        """运行命令行交互模式"""
        print("\n" + "=" * 70)
        print("🤖 DSL聊天机器人 - 命令行模式")
        print("=" * 70)
        print(f"💡 提示: 系统将在{self.timeout_minutes}分钟无操作后自动退出")
        print("输入 '退出' 或 'exit' 结束对话")
        print("-" * 70)

        self.is_running = True
        self.start_activity_monitor()

        try:
            # 执行初始脚本显示欢迎消息
            initial_replies = self.controller._execute_script()
            for reply in initial_replies:
                print(f"🤖🤖 机器人: {reply}")

            # 主循环
            while self.is_running and not self.controller.runtime.should_exit:
                try:
                    # 获取用户输入
                    user_input = input("\n👤👤 您: ").strip()

                    # 记录用户活动
                    self.record_user_activity()

                    if not user_input:
                        continue

                    # 检查退出命令
                    if user_input.lower() in ['退出', 'exit', 'quit', 'bye']:
                        print("\n👋👋 感谢使用，再见！")
                        break

                    # 处理用户输入
                    self.controller.runtime.set_variable("$user_input", user_input)
                    replies = self.controller._execute_script()

                    # 输出回复
                    for reply in replies:
                        print(f"🤖🤖 机器人: {reply}")

                except KeyboardInterrupt:
                    print("\n\n👋👋 用户中断，退出系统")
                    break
                except Exception as e:
                    print(f"❌❌ 系统错误: {e}")
                    print("💡💡 您可以继续输入或输入'退出'结束对话")

        finally:
            self.cleanup()

    def run_gui_mode(self):
        """运行图形界面模式"""
        print("🚀 启动图形界面模式...")

        self.is_running = True

        try:
            # 创建GUI实例
            self.gui = ChatbotGUI(
                script_path=self.script_path,
                llm_api_key=self.llm_api_key
            )

            # 设置活动记录回调
            self._setup_gui_activity_monitor()

            # 启动超时监控
            self.start_activity_monitor()

            # 运行GUI主循环
            self.gui.run()

        except Exception as e:
            print(f"❌ GUI模式启动失败: {e}")
        finally:
            self.cleanup()

    def _setup_gui_activity_monitor(self):
        """设置GUI活动监控"""
        if not self.gui:
            return

        # 重写GUI的输入处理方法，加入活动记录
        original_process_input = self.gui.process_user_input

        def new_process_input(user_input):
            self.record_user_activity()
            return original_process_input(user_input)

        self.gui.process_user_input = new_process_input

        # 重写其他可能产生用户活动的方法
        original_on_send = self.gui.on_send_message

        def new_on_send(event=None):
            self.record_user_activity()
            return original_on_send(event)

        self.gui.on_send_message = new_on_send

    def cleanup(self):
        """清理资源"""
        self.is_running = False

        if self.timeout_timer:
            self.timeout_timer.cancel()
            self.timeout_timer = None

        print("🧹 应用程序资源清理完成")


def main():
    """主函数 - 程序入口点"""

    # 配置参数
    SCRIPT_PATH = "C:/Users/hotma/Desktop/DSL/end/DSL2.txt"  # 默认脚本路径

    LLM_API_KEY = os.getenv("sk-5dd634970d3e447b99b7e9ad631a5e80")  # 从环境变量获取API密钥
    TIMEOUT_MINUTES = 15  # 默认15分钟无操作自动退出

    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description="DSL聊天机器人应用程序")
    parser.add_argument("--script", "-s", default=SCRIPT_PATH,
                        help="DSL脚本文件路径 (默认: scripts/chatbot.dsl)")
    parser.add_argument("--api-key", "-k", default=LLM_API_KEY,
                        help="DeepSeek API密钥 (默认: 从环境变量DEEPSEEK_API_KEY获取)")
    parser.add_argument("--mode", "-m", choices=["cli", "gui"], default="gui",
                        help="运行模式: cli(命令行) 或 gui(图形界面) (默认: gui)")
    parser.add_argument("--timeout", "-t", type=int, default=TIMEOUT_MINUTES,
                        help=f"无操作超时时间(分钟) (默认: {TIMEOUT_MINUTES}分钟)")
    parser.add_argument("--no-timeout", action="store_true",
                        help="禁用超时自动退出功能")

    args = parser.parse_args()
    print('ok')
    # 处理超时设置
    if args.no_timeout:
        timeout_minutes = 0  # 0表示禁用超时
    else:
        timeout_minutes = args.timeout

    try:
        # 创建应用程序实例
        app = DSLApplication(
            script_path=args.script,
            llm_api_key=args.api_key,
            timeout_minutes=timeout_minutes
        )

        # 初始化组件
        app.initialize_components()

        # 根据模式运行
        if args.mode == "cli":
            app.run_cli_mode()
        else:
            app.run_gui_mode()

    except FileNotFoundError as e:
        print(f"❌ 文件错误: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 用户中断程序")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 程序运行错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()