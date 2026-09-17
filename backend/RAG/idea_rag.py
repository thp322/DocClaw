import os
import sys
import json

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_CURRENT_DIR))
sys.path.insert(0, _PROJECT_ROOT)          # -> import config_data
sys.path.insert(0, _CURRENT_DIR)           # -> from file_history_store import ...

from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_models.tongyi import ChatTongyi

from file_history_store import get_history, build_history_saver
import config_data as config



DESC_PREFIX = "【DESC】"

def print_prompt(prompt):
    print(prompt.to_string())
    print("="*20)
    return prompt


def format_requirement_json(json_text):
    data = json.loads(json_text)

    # 需求数组统一转成 Markdown 列表；空数组给占位文案
    def _numbered(items):
        return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1)) if items else "暂无"

    def _bulleted(items):
        return "\n".join(f"- {item}" for item in items) if items else "暂无"

    return (
        f"## 📋 需求拆解：{data['product_name']}\n\n"
        f"**🎯 目标用户**\n\n{data['target_user']}\n\n"
        f"**🔥 用户痛点**\n\n{data['pain_point']}\n\n"
        f"**⚙️ 核心功能需求**\n\n{_numbered(data['functional_requirements'])}\n\n"
        f"**🛡️ 非功能需求**\n\n{_bulleted(data['non_functional_requirements'])}\n\n"
        f"**🚀 业务目标**\n\n{data['business_goal']}"
    )


class IdeaRag(object):
    def __init__(self):

        self.describe_prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", """
                    你是资深的产品经理，你特别擅长将用户模糊的idea转化成初级产品描述。你需要基于用户的一个模糊的产品想法+历史对话信息，逐步收集信息，最终确定用户需要做一款什么样的产品。
                    
                    规则：
                    1. 每次只提出【1个】问题，优先询问当前缺失的最重要信息，不要一次性问多个问题，不要问用户已经回答过的内容。
                    2. 持续收集信息，直到目标维度信息基本完备。需要补齐的维度清单：目标用户是谁、业务场景、核心痛点、产品核心能力、使用终端、权限/业务约束。
                    3. 当信息已经足够完整，且你已经很确定用户需要做一款什么样的产品了，不再提问，直接输出一段通顺完整且详细的初级产品描述。
                    
                    初级产品描述要求：
                    - 保留用户核心诉求，严禁编造不存在的功能；
                    - 输出单独一段文字，不要分点；
                    - 必须包含：产品目标用户、核心解决的痛点、产品主要能力。
            
                    输出格式强制规则：
                    - 若需要继续追问：固定以【QUESTION】开头，后面跟1个问题。不要多余解释。示例：【QUESTION】这个工具的目标使用人群是哪些岗位？
                    - 若信息充足：固定以【DESC】开头，后面跟初级产品描述正文。示例：【DESC】本产品是面向企业销售团队……
                """),
                ("system", "并且我提供用户的对话历史记录，如下："),
                MessagesPlaceholder("history"),
                ("user", "用户的输入：{input}")
            ]
        )

        self.idea_prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", """
                    你是资深的产品经理。基于下面的初级产品描述，拆解产品需求，输出严格JSON，禁止输出任何额外文字、注释、markdown标记，禁止使用```代码块包裹。
                    JSON字段定义：
                    - product_name：产品暂定名称（简短）
                    - target_user：目标用户
                    - pain_point：用户痛点
                    - functional_requirements：数组，每一项是一条功能需求
                    - non_functional_requirements：数组，非功能需求（性能、安全、易用等，没有就空数组）
                    - business_goal：产品业务目标
                    
                    只输出JSON：
                """),
                ("user", "初级产品描述：{product_description}")
            ]
        )

        self.chat_model = ChatTongyi(model=config.chat_model_name, streaming=True)

        # 阶段一链：模糊 idea -> 多轮追问 -> 初级产品描述（挂文件历史）
        self.chain = self.__get_chain()
        # 阶段二链：初级产品描述 -> 需求拆解 JSON（不挂文件历史）
        self.breakdown_chain = self.__get_breakdown_chain()

    def read_history(self, session_config):
        history_str = ''
        session_id = session_config["configurable"]["session_id"]
        history_store = get_history(session_id)
        messages = history_store.messages

        role_names = {"human": "用户", "ai": "AI", "system": "系统"}
        # print(f"会话 {session_id} 共 {len(messages)} 条历史消息")
        # print("=" * 20)
        for msg in messages:
            print(f"{role_names.get(msg.type, msg.type)}：{msg.content}")
            msg_content = msg.content
            history_str += msg_content
        # print("=" * 20)

        return history_str

    def __get_chain(self):
        """获取最终的执行链"""

        chain = self.describe_prompt_template | print_prompt | self.chat_model | StrOutputParser()

        conversation_chain = RunnableWithMessageHistory(
            chain,
            get_history,
            input_messages_key="input",
            history_messages_key="history",
        )

        return conversation_chain

    def __get_breakdown_chain(self):
        """阶段二链"""
        return (
            self.idea_prompt_template
            | print_prompt
            | self.chat_model
            | StrOutputParser()
            | format_requirement_json
        )

    def chat_stream(self, user_input, session_config):
        """阶段一流式对话"""
        yield from self.chain.stream({"input": user_input}, session_config)

    def breakdown_stream(self, product_description, session_config):
        """阶段二流式对话：输出格式化需求卡片，流结束后保存会话快照"""
        session_id = session_config["configurable"]["session_id"]
        chain = self.breakdown_chain | build_history_saver("需求拆解", session_id)
        yield from chain.stream({"product_description": product_description})




if __name__ == '__main__':
    session_config = session_config = {
        "configurable": {
            "session_id": "cf75e97bdcf74e3f893de8a1b6ada5a4",
        }
    }
    # 测试后端 RAG
    # res = IdeaRag().chain.invoke({"input": "面向独立开发者的AI笔记工具"}, session_config)
    # print(res)

    # 查看历史记录
    messages = IdeaRag().read_history(session_config)

