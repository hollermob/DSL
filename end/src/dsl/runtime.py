from typing import Dict, Any, Optional ,List

class RuntimeEnvironment:
    """运行时环境：为DSL脚本执行提供'内存'"""

    def __init__(self):
        # 变量存储：存储脚本中定义的所有变量
        self.variables: Dict[str, Any] = {}
        # 标签表：存储标签名到语句索引的映射
        self.labels: Dict[str, int] = {}
        # 当前执行位置
        self.current_line = 0
        # 程序是否应该退出
        self.should_exit = False
        # 用于存储临时的回复消息
        self.last_reply: Optional[str] = None
        # 意图定义存储
        self.defined_intents: List[str] = []

    def set_defined_intents(self, intents: List[str]):
        """设置定义的意图列表"""
        self.defined_intents = intents

    def get_defined_intents(self) -> List[str]:
        """获取定义的意图列表"""
        return self.defined_intents.copy()  # 返回副本避免外部修改

    def set_variable(self, name: str, value: Any):
        """设置变量值"""
        # 去掉变量名的$前缀（如果存在）
        if name.startswith('$'):
            name = name[1:]
        self.variables[name] = value

    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量值"""
        if name.startswith('$'):
            name = name[1:]
        return self.variables.get(name, default)

    def register_label(self, label_name: str, line_number: int):
        """注册标签位置"""
        self.labels[label_name] = line_number

    def jump_to_label(self, label_name: str) -> bool:
        """跳转到指定标签"""
        if label_name in self.labels:
            self.current_line = self.labels[label_name]
            return True
        return False

    def set_reply(self, message: str):
        """设置回复消息"""
        self.last_reply = message

    def get_reply(self) -> Optional[str]:
        """获取并清空回复消息"""
        reply = self.last_reply
        self.last_reply = None
        return reply

    def reset(self):
        """重置运行时环境"""
        self.variables.clear()
        self.labels.clear()
        self.current_line = 0
        self.should_exit = False
        self.last_reply = None
