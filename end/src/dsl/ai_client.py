import os
import json
from typing import List, Optional
from openai import OpenAI

# 设置API密钥
os.environ["DEEPSEEK_API_KEY"] = "sk-5dd634970d3e447b99b7e9ad631a5e80"


class IntentClassifier:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.deepseek.com"):
        """
        初始化DeepSeek意图分类器

        Args:
            api_key: DeepSeek API密钥，如果不提供则从环境变量读取
            base_url: API基础URL
        """
        api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("请设置DEEPSEEK_API_KEY环境变量或传递api_key参数")

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

    def get_intent(self, message: str, may_intent: List[str]) -> str:
        """
        识别用户消息的意图

        Args:
            message: 用户输入的消息
            may_intent: 可能的意图列表

        Returns:
            最匹配的意图字符串
        """

        # 构建系统提示词
        system_prompt = """你是一个意图分类助手。你的任务是从给定的意图列表中，选择最符合用户消息的意图。

规则：
1. 只能返回意图列表中存在的字符串
2. 不要添加任何解释或额外文本
3. 如果消息明显不符合任何意图，返回"其他信息"
4. 如果有多个意图存在，判断哪个最重要（比如，识别到"问候"和“查询商品”，显然“查询商品”才是用户主要想要的），如果同样重要，则以返回第一个意图
5. 用户可能会给出否定句（如“不退出”），这种情况下，你可以将它归为“其他”

意图列表：""" + ", ".join(may_intent)

        try:
            # 调用DeepSeek API
            response = self.client.chat.completions.create(
                model="deepseek-chat",  # 或其他DeepSeek模型
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.1,  # 较低的温度使结果更稳定
                max_tokens=50
            )

            # 提取回复
            result = response.choices[0].message.content.strip()
            # 验证结果是否在意图列表中
            if result in may_intent:
                return result
            else:
                # 如果返回的不在列表中，尝试查找最相似的
                return "其他"

        except Exception as e:
            print(f"API调用错误: {e}")
            return "其他"
