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
embedding_model_name = "text-embedding-v4"
chat_model_name = "qwen3-max"

