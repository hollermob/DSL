import os
import sys
from typing import Optional
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
from datetime import datetime

# 导入主控制器
from main_controller import DSLController


class ChatbotGUI:
    """聊天机器人图形用户界面"""

    def __init__(self, script_path: str, llm_api_key: Optional[str] = None):
        self.root = tk.Tk()
        self.root.title("🤖 DSL聊天机器人")
        self.root.geometry("800x600")

        self.script_path = script_path
        self.llm_api_key = llm_api_key
        self.controller: Optional[DSLController] = None

        # 设置样式
        self.setup_styles()

        # 创建界面
        self.create_widgets()

        # 初始化系统
        self.initialize_system()

    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        style.theme_use('clam')

        # 颜色方案
        self.bg_color = "#f0f0f0"
        self.bot_color = "#e3f2fd"
        self.user_color = "#f3e5f5"
        self.text_color = "#333333"

    def create_widgets(self):
        """创建界面组件"""
        # 设置背景色
        self.root.configure(bg=self.bg_color)

        # 标题栏
        title_frame = tk.Frame(self.root, bg="#1976d2", height=60)
        title_frame.pack(fill=tk.X, side=tk.TOP)
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="🤖 DSL智能聊天机器人",
            font=("Microsoft YaHei", 18, "bold"),
            fg="white",
            bg="#1976d2"
        )
        title_label.pack(pady=15)

        # 状态栏
        self.status_frame = tk.Frame(self.root, bg="#e0e0e0", height=30)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_frame.pack_propagate(False)

        self.status_label = tk.Label(
            self.status_frame,
            text="正在初始化系统...",
            font=("Microsoft YaHei", 10),
            fg="#666666",
            bg="#e0e0e0"
        )
        self.status_label.pack(side=tk.LEFT, padx=10)

        # 对话显示区域
        chat_frame = tk.Frame(self.root, bg=self.bg_color)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 添加滚动文本框
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=("Microsoft YaHei", 11),
            bg="white",
            fg=self.text_color,
            state=tk.DISABLED,
            height=20
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        # 输入区域
        input_frame = tk.Frame(self.root, bg=self.bg_color)
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # 输入框
        self.input_entry = tk.Entry(
            input_frame,
            font=("Microsoft YaHei", 12),
            bg="white",
            fg=self.text_color,
            relief=tk.SOLID,
            borderwidth=1
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.input_entry.bind("<Return>", self.on_send_message)

        # 发送按钮
        send_button = ttk.Button(
            input_frame,
            text="发送",
            command=self.on_send_message,
            style="Accent.TButton"
        )
        send_button.pack(side=tk.RIGHT)

        # 控制按钮区域
        control_frame = tk.Frame(self.root, bg=self.bg_color)
        control_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # 清空按钮
        clear_button = ttk.Button(
            control_frame,
            text="清空对话",
            command=self.clear_conversation,
            style="TButton"
        )
        clear_button.pack(side=tk.LEFT, padx=(0, 10))

        # 重置按钮
        reset_button = ttk.Button(
            control_frame,
            text="重置系统",
            command=self.reset_system,
            style="TButton"
        )
        reset_button.pack(side=tk.LEFT, padx=(0, 10))

        # 查看历史按钮
        history_button = ttk.Button(
            control_frame,
            text="对话历史",
            command=self.show_history,
            style="TButton"
        )
        history_button.pack(side=tk.LEFT)

        # 退出按钮
        exit_button = ttk.Button(
            control_frame,
            text="退出",
            command=self.on_exit,
            style="TButton"
        )
        exit_button.pack(side=tk.RIGHT)

    def initialize_system(self):
        """初始化系统"""
        try:
            # 创建控制器
            self.controller = DSLController(
                script_path=self.script_path,
                llm_api_key=self.llm_api_key
            )

            # 初始化
            self.controller.initialize()

            # 显示欢迎消息
            self.update_status("系统就绪，请输入消息...")
            self.add_message("🤖 机器人", "您好！我是DSL聊天助手，请输入任意信息开始我们的聊天:)", is_bot=True)


        except Exception as e:
            messagebox.showerror("初始化错误", f"系统初始化失败:\n{str(e)}")
            self.root.quit()

    def update_status(self, message: str):
        """更新状态栏"""
        self.status_label.config(text=message)
        self.root.update()

    def add_message(self, sender: str, message: str, is_bot: bool = False):
        """添加消息到聊天窗口"""
        self.chat_display.config(state=tk.NORMAL)

        # 获取当前时间
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 设置标签
        tag_name = "bot" if is_bot else "user"
        bg_color = self.bot_color if is_bot else self.user_color

        # 配置标签样式
        self.chat_display.tag_config(tag_name,
                                     background=bg_color,
                                     relief=tk.RIDGE,
                                     borderwidth=1,
                                     lmargin1=10,
                                     lmargin2=10,
                                     rmargin=10,
                                     spacing1=5,
                                     spacing3=5
                                     )

        # 插入消息
        self.chat_display.insert(tk.END, f"[{timestamp}] {sender}:\n", tag_name)
        self.chat_display.insert(tk.END, f"{message}\n\n", tag_name)

        # 滚动到底部
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def on_send_message(self, event=None):
        """发送消息处理"""
        user_input = self.input_entry.get().strip()
        if not user_input:
            return

        # 清空输入框
        self.input_entry.delete(0, tk.END)

        # 显示用户消息
        self.add_message("👤 您", user_input, is_bot=False)

        # 处理用户输入
        self.process_user_input(user_input)

    def process_user_input(self, user_input: str):
        """处理用户输入"""
        if not self.controller:
            self.add_message("🤖 机器人", "系统未初始化，请重启程序。", is_bot=True)
            return

        try:
            # 检查退出命令
            if user_input.lower() in ['退出', 'exit', 'quit', 'bye']:
                self.add_message("🤖 机器人", "👋 感谢使用，再见！", is_bot=True)
                self.root.after(2000, self.on_exit)
                return

            # 更新状态
            self.update_status("正在处理您的消息...")

            # 设置用户输入变量
            self.controller.runtime.set_variable("$user_input", user_input)

            # # 执行脚本
            # replies = self.controller._execute_script()

            # # 显示机器人回复
            # for reply in replies:
            #     self.add_message("🤖 机器人", reply, is_bot=True)

            # # 恢复状态
            # self.update_status("系统就绪，请输入消息...")
            # 第一步：执行到get_intent并暂停
            replies = self.controller._execute_script()

            # 显示已经产生的回复（如果有）
            for reply in replies:
                self.add_message("🤖 机器人", reply, is_bot=True)

            # 检查是否在get_intent处暂停
            if self.controller.interpreter.is_execution_paused() and \
                    self.controller.interpreter.get_pause_reason() == "get_intent":

                # 显示意图识别中...
                self.update_status("正在识别您的意图...")

                # 手动触发意图识别
                input_text = self.controller.runtime.get_variable("$user_input", "")

                # 使用LLM识别意图
                if self.controller.llm_classifier:
                    try:
                        intent = self.controller.llm_classifier.get_intent(
                            input_text,
                            self.controller.dsl_intents
                        )
                        print(f"🤖 LLM识别意图: {intent}")

                        # 设置意图变量
                        self.controller.runtime.set_variable("$intent", intent)

                        # 恢复执行（继续执行if判断等）
                        self.controller.interpreter.resume_execution()

                        # 继续执行剩余脚本
                        self.update_status("正在生成回复...")
                        more_replies = self.controller._execute_script()


                        # 显示剩余的回复
                        for reply in more_replies:
                            self.add_message("🤖 机器人", reply, is_bot=True)

                    except Exception as e:
                        print(f"⚠️ LLM识别失败: {e}")
                        self.add_message("🤖 机器人",
                                             "抱歉，意图识别失败，请重新输入。",
                                             is_bot=True)
                    # else:
                    #     self.add_message("🤖 机器人",
                    #                  "意图识别模块未初始化。",
                    #                  is_bot=True)

            # 恢复状态
            self.update_status("系统就绪，请输入消息...")

        except Exception as e:
            error_msg = f"抱歉，处理消息时出现错误: {str(e)}"
            self.add_message("🤖 机器人", error_msg, is_bot=True)
            self.update_status("系统错误，请重试...")

    def clear_conversation(self):
        """清空对话"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)

        if self.controller:
            self.controller.reset_conversation()
            self.add_message("🤖 机器人", "对话已清空，有什么可以帮助您？", is_bot=True)

        messagebox.showinfo("清空对话", "对话记录已清空")

    def reset_system(self):
        """重置系统"""
        if messagebox.askyesno("重置系统", "确定要重置系统吗？这将清空所有对话和状态。"):
            self.clear_conversation()
            self.initialize_system()

    def show_history(self):
        """显示对话历史"""
        if not self.controller:
            return

        history = self.controller.get_conversation_history()

        # 创建历史窗口
        history_window = tk.Toplevel(self.root)
        history_window.title("对话历史")
        history_window.geometry("600x400")

        # 创建文本框显示历史
        history_text = scrolledtext.ScrolledText(
            history_window,
            wrap=tk.WORD,
            font=("Microsoft YaHei", 10),
            bg="white",
            fg=self.text_color
        )
        history_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 显示历史记录
        for item in history:
            role = "用户" if item['role'] == 'user' else "机器人"
            history_text.insert(tk.END,
                                f"[{item['timestamp']}] {role}: {item['message']}\n{'=' * 50}\n"
                                )

        history_text.config(state=tk.DISABLED)

    def on_exit(self):
        """退出程序"""
        if messagebox.askyesno("退出", "确定要退出程序吗？"):
            self.root.quit()

    def run(self):
        """运行主循环"""
        self.root.mainloop()