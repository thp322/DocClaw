"""
1,knowledge_base.py
"""
# md5 文件路径
md5_path = "./md5.text"

# Chroma
collection_name = "rag"
persist_directory = "./chroma_db"

# spliter
chunk_size = 1000               # 分割后的文本段最大长度
chunk_overlap = 100             # 连续文本段之间的字符重叠数量
separators = ["\n\n", "\n", ".", "!", "?", "。", "！", "？", " ", ""]   # 自然段落划分的符号

max_split_char_number = 1000    # 文本分割的阈值

operator = "Harper"


"""
2,vector_stores.py
"""
similarity_threshold = 1            # 检索返回匹配的文档数量（相似度度检索）


"""
3,rag.py
"""

# ---- 聊天模型 ----
CHAT_MODELS = [
    {"id": "qwen3.7-flash", "name": "Qwen3.7 Flash · 轻量"},
    {"id": "qwen3.7-plus",  "name": "Qwen3.7 Plus · 均衡", "default": True},
    {"id": "qwen3.7-max",   "name": "Qwen3.7 Max · 旗舰"},
    {"id": "qwen3.8-flash", "name": "Qwen3.8 Flash · 最新"},
    {"id": "qwen3.8-max",   "name": "Qwen3.8 Max · 最新"},
]

# ---- 嵌入模型 ----
EMBEDDING_MODELS = [
    {"id": "qwen3.7-text-embedding", "name": "Qwen3.7 Text Embedding", "default": True},
]

# 默认模型：无前端选择时（如后端 __main__ 调试）使用
dashscope_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
default_chat_model = next(m["id"] for m in CHAT_MODELS if m.get("default"))
embedding_model_name = next(m["id"] for m in EMBEDDING_MODELS if m.get("default"))

