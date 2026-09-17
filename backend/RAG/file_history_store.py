import json
import os
from datetime import datetime
from typing import Sequence
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    message_to_dict,
    messages_from_dict,
)


# 历史存储固定放在【项目根目录/chat_history】，与启动时的工作目录无关。
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_CURRENT_DIR))
_CHAT_HISTORY_DIR = os.path.join(_PROJECT_ROOT, "chat_history")
_HISTORY_RECORD_DIR = os.path.join(_CHAT_HISTORY_DIR, "history")


def get_history(session_id):
    return FileChatMessageHistory(session_id, _CHAT_HISTORY_DIR)


def save_conversation_record(session_id, source):
    """保存一次会话快照到 chat_history/history/ 目录"""
    now = datetime.now()
    file_name = f"{now.strftime('%Y%m%d_%H%M%S')}_{source}.json"
    file_path = os.path.join(_HISTORY_RECORD_DIR, file_name)
    os.makedirs(_HISTORY_RECORD_DIR, exist_ok=True)

    # 从该会话的多轮消息文件读取完整对话记录
    role_map = {"human": "user", "ai": "assistant", "system": "system"}
    messages = [
        {"role": role_map.get(msg.type, msg.type), "content": msg.content}
        for msg in get_history(session_id).messages
    ]

    record = {
        "session_id": session_id,
        "source": source,
        "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "messages": messages,
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    return file_path


def build_history_saver(source, session_id):
    """构造一个可挂在任意 LCEL 链末尾的「会话快照保存」节点"""
    def _save_node(chain_output):
        # 阶段二链对话补录进会话
        if isinstance(chain_output, str) and chain_output.strip():
            get_history(session_id).add_messages([AIMessage(content=chain_output)])
        save_conversation_record(session_id, source)
        return chain_output

    return _save_node


def list_conversation_records():
    """列出 history 目录下的全部会话快照，按对话时间倒序"""
    if not os.path.isdir(_HISTORY_RECORD_DIR):
        return []

    records = []
    for file_name in os.listdir(_HISTORY_RECORD_DIR):
        if not file_name.endswith(".json"):
            continue
        try:
            with open(os.path.join(_HISTORY_RECORD_DIR, file_name), "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        messages = data.get("messages", [])
        # 列表预览：取第一条用户消息
        preview = next(
            (m.get("content", "") for m in messages if m.get("role") == "user"),
            "",
        )
        records.append({
            "file_name": file_name,
            "session_id": data.get("session_id", ""),
            "source": data.get("source", "未知来源"),
            "created_at": data.get("created_at", ""),
            "message_count": len(messages),
            "preview": preview,
        })

    # 文件名前缀为 YYYYMMDD_HHMMSS，按文件名倒序即对话时间倒序
    records.sort(key=lambda item: item["file_name"], reverse=True)
    return records


def load_conversation_record(file_name):
    """按文件名读取单条会话快照（basename 处理，防止目录穿越）"""
    safe_name = os.path.basename(file_name)
    with open(os.path.join(_HISTORY_RECORD_DIR, safe_name), "r", encoding="utf-8") as f:
        return json.load(f)


def delete_conversation_record(file_name):
    """删除一条历史记录：同时删除 history 快照和 chat_history 下的会话消息文件

    Args:
        file_name: history 目录下的快照文件名

    Returns:
        tuple(snapshot_deleted: bool, session_deleted: bool)
        快照文件不存在抛 FileNotFoundError；会话消息文件可能已被清理，缺失不算错误。
    """
    safe_name = os.path.basename(file_name)
    snapshot_path = os.path.join(_HISTORY_RECORD_DIR, safe_name)

    # 先读快照拿 session_id，再删快照（顺序不能反）
    with open(snapshot_path, "r", encoding="utf-8") as f:
        record = json.load(f)

    os.remove(snapshot_path)

    # 会话 id 同样做 basename 防护，限定在 chat_history 目录内
    session_id = os.path.basename(record.get("session_id", ""))
    session_path = os.path.join(_CHAT_HISTORY_DIR, session_id) if session_id else ""
    session_deleted = bool(session_path) and os.path.isfile(session_path)
    if session_deleted:
        os.remove(session_path)

    return True, session_deleted


class FileChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, session_id, storage_path):
        self.session_id = session_id        # 会话 id
        self.storage_path = storage_path    # 不同会话 id 的存储文件，所在的文件夹路径
        # 完整的文件路径
        self.file_path = os.path.join(self.storage_path, self.session_id)

        # 确保文件夹是存在的
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        # Sequence序列 类似list、tuple
        all_messages = list(self.messages)      # 已有的消息列表
        all_messages.extend(messages)           # 新的和已有的融合成一个 list

        # 将数据同步写入到本地文件中
        # 类对象写入文件 -> 一堆二进制
        # 为了方便，可以将 BaseMessage 消息转为字典（借助 json 模块以 json 字符串写入文件）
        # 官方message_to_dict：单个消息对象（BaseMessage 类实例） -> 字典
        # new_messages = []
        # for message in all_messages:
        #     d = message_to_dict(message)
        #     new_messages.append(d)

        new_messages = [message_to_dict(message) for message in all_messages]
        # 将数据写入文件
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(new_messages, f)

    @property       # @property 装饰器将 messages 方法变成成员属性用
    def messages(self) -> list[BaseMessage]:
        # 当前文件内： list[字典]
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                messages_data = json.load(f)    # 返回值就是：list[字典]
                return messages_from_dict(messages_data)
        except FileNotFoundError:
            return []

    def clear(self) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump([], f)
