"""
DocClaw Streamlit 前端
======================

两种模式：
  1. 落地页（landing）   — 无侧边栏、大标题、特性卡片
  2. 工作页（workspace） — 固定满高侧边栏 + 居中输入区

运行：
  cd DocClaw && streamlit run frontend/app.py

────────────────────────────────────────────────────────────────
1. 「session_state」：
   Streamlit 每次用户交互都会把整个脚本重新执行一遍。session_state
   是唯一的跨重跑记忆要让数据在重跑之间存活它是一个绑定当前浏览器会话的
   字典

3. 「widget key」：
   每个 Streamlit 组件可传 key 参数作为唯一标识。好处：
   a) 用户输入的值会自动存入 st.session_state[key]，重跑后不丢失
   b) 代码里可随时读写 st.session_state[key] 来控制组件内容
   同一个 key 在一次运行里出现两次会直接报错

4. 「st.rerun()」：
   立即终止当前这次运行，从头再执行一遍脚本。典型用法：
   在状态 A 里修改 session_state → rerun → 下一次运行读到新状态，
   渲染出状态 B 的界面
────────────────────────────────────────────────────────────────
"""

import os
import sys
import base64

# __file__ 是当前模块文件路径；os.path.abspath 把它转成绝对路径
# os.path.dirname 取上级目录。这样无论从哪个工作目录启动脚本
_FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))   # .../DocClaw/frontend
_ROOT_DIR = os.path.dirname(_FRONTEND_DIR)                   # .../DocClaw
_PUBLIC_DIR = os.path.join(_ROOT_DIR, "public")              # 静态资源目录
_BACKEND_RAG_DIR = os.path.join(_ROOT_DIR, "backend", "RAG")

# Python 默认只从脚本所在目录 + site-packages 找模块
# 用 `streamlit run frontend/app.py` 启动时 Streamlit 会自动把 app.py 所在目录加入搜索路径
# 保证在任何启动方式下都能找到同目录的 styles.py
sys.path.insert(0, _FRONTEND_DIR)
sys.path.insert(0, _ROOT_DIR)
sys.path.insert(0, _BACKEND_RAG_DIR)

import uuid
import streamlit as st

from styles import inject_css 
import config_data as config
from idea_rag import IdeaRag, DESC_PREFIX
from file_history_store import (
    list_conversation_records,
    load_conversation_record,
    delete_conversation_record,
)
from html import escape as _html_escape

# ============================================================
# Streamlit 全局配置
# ============================================================
# st.set_page_config 必须是第一个被调用的 Streamlit 命令
_FAVICON_PATH = os.path.join(_PUBLIC_DIR, "favicon.ico")
st.set_page_config(
    page_title="DocClaw · 产品文档智能维护 Agent",   
    # 页签图标：本地图标文件存在就用文件，否则退化为 emoji
    page_icon=_FAVICON_PATH,
    layout="wide",                     # 宽屏布局（默认 "centered" 内容较窄）
    initial_sidebar_state="expanded",  # 侧边栏初始展开
)


def _img_to_base64(path: str) -> str:
    """本地图片转 data URI（Streamlit 无法用本地路径渲染 HTML <img>）"""
    # 图片缺失时返回空串，跳过渲染
    if not os.path.exists(path):
        return ""  

    # 根据扩展名查 MIME 类型（浏览器靠它决定如何解码）
    # dict.get(key, 默认值)：查不到时给 image/png 兜底
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "ico": "image/x-icon", "svg": "image/svg+xml"}.get(
        # os.path.splitext("a.png") -> ("a", ".png")；去点、转小写做 key
        os.path.splitext(path)[1].lower().lstrip("."), "image/png")

    # "rb" 二进制读（图片不是文本）；b64encode 后 .decode("ascii")
    # 把 bytes 转成纯 ASCII 字符串，才能安全拼进 HTML/URL
    with open(path, "rb") as f:
        return f"data:{mime};base64,{base64.b64encode(f.read()).decode('ascii')}"


# ============================================================
# 1. 落地页
# ============================================================

# 线性 SVG 图标模板：{} 是 str.format 的占位符，运行时填入各图标的
_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
        'stroke-linejoin="round">{}</svg>')
# 六个特性图标的 SVG 图形定义
FEATURE_ICONS = {
    "bulb":     _SVG.format('<path d="M15 14c.2-1 .7-1.7 1.5-2.5C17.5 10.6 18 9.3 18 8A6 6 0 0 0 6 8c0 1.3.5 2.6 1.5 3.5.8.8 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/>'),
    "search":   _SVG.format('<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>'),
    "file":     _SVG.format('<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>'),
    "arrows":   _SVG.format('<path d="M8 3 4 7l4 4"/><path d="M4 7h16"/><path d="m16 21 4-4-4-4"/><path d="M20 17H4"/>'),
    "database": _SVG.format('<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/>'),
    "layers":   _SVG.format('<path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>'),
}

# 特性卡片内容
FEATURES = [
    ("bulb",     "需求智能拆解", "一句话想法 → 用户故事 + 功能列表 + 优先级"),
    ("search",   "竞品情报收集", "自动发现竞品、抓取官网动态、生成对比矩阵"),
    ("file",     "PRD 生成升级", "从无到有生成 PRD，或基于旧版本智能升级"),
    ("arrows",   "变更影响评估", "改了需求？自动评估上下游影响，给出缓解建议"),
    ("database", "产品记忆沉淀", "决策、调研、技术选型自动入库，下次直接复用"),
    ("layers",   "多源文档管理", "本地 + Wiki + 对象存储，一处保存处处同步"),
]


def render_landing():
    """落地页：注入 CSS """
    # 见 styles.py
    inject_css("landing")

    st.markdown("""
    <div>
        <h1 class="hero-title">让产品文档<br>自己活起来</h1>
        <p class="hero-subtitle">
            DocClaw — 产品文档全生命周期 Agent<br>
            需求拆解 · 竞品调研 · PRD 生成 · 影响评估 · 记忆沉淀 · 文档管理
        </p>
    </div>
    """, unsafe_allow_html=True)  # unsafe_allow_html=True 允许 markdown 里写原生 HTML，False 时 HTML 会被原样显示为文本

    # st.button 的返回值：只在点击后的那次运行中为 True，其余时候都是 False
    # 点击后：把 entered 存入 session_state → rerun → main() 里读到，entered=True，渲染工作页
    # key="cta_start"：给按钮唯一 ID，Streamlit 靠它区分页面上的多个按钮
    if st.button("开始制作", key="cta_start", type="primary"):
        st.session_state["entered"] = True
        st.rerun()    # 立即重跑脚本，让新状态马上生效

    # 卡片 HTML 必须拼成【一整行】（字符串之间不能夹换行空行）：
    # markdown-it 渲染 HTML 块时遇到空行会认为 HTML 块提前结束，
    # 导致网格 <div> 被拆碎、样式失效。
    # "".join(生成器)：循环拼接六张卡片的 HTML，比 for 循环 += 更高效。
    cards = "".join(
        f'<div class="feature-card">'
        f'<div class="feature-icon">{FEATURE_ICONS[icon]}</div>'
        f'<div class="feature-title">{title}</div>'
        f'<div class="feature-desc">{desc}</div>'
        f'</div>'
        for icon, title, desc in FEATURES
    )
    st.markdown(f'<div class="feature-grid">{cards}</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="footer-text">
        DocClaw · 基于 LangChain + Chroma 构建 · By · Harper · 2026
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# 2. 侧边栏：Logo + 导航
# ============================================================

# 功能导航配置表
# key 是页面标识（存入 session_state["page"]）
FUNC_PAGES = {
    "idea":      {"icon": "lightbulb",      "label": "需求拆解"},
    "research":  {"icon": "search",         "label": "竞品调研"},
    "prd":       {"icon": "description",    "label": "PRD 生成"},
    "impact":    {"icon": "compare_arrows", "label": "变更评估"},
    "memory":    {"icon": "psychology",     "label": "产品记忆"},
    "workspace": {"icon": "layers",         "label": "文档工作台"},
}

# 资源导航配置表
RESOURCE_PAGES = {
    "history": {"icon": "history", "label": "历史记录"},
    "contact": {"icon": "contact_mail", "label": "联系我们"},
}

# 合并两张表为"全部占位页"查询表：{**a, **b} 是字典解包合并语法，键重复时后者覆盖
ALL_PAGES = {**FUNC_PAGES, **RESOURCE_PAGES}


def _nav_button(label: str, key: str, icon: str, page: str):
    """渲染一个侧边栏导航按钮（被三个板块复用）"""
    if st.sidebar.button(label, key=key, use_container_width=True, icon=icon):
        # 记录目标页到 session_state，rerun 后 render_workspace()
        # 读取 page 并渲染对应页面
        st.session_state["page"] = page
        # 离开/进入页面时复位历史记录页的「列表-详情」选中态
        st.session_state.pop("history_selected", None)
        st.rerun()


def render_sidebar():
    """侧边栏：Logo + 三个板块的导航按钮 + 版本号"""
    # 注入工作页专属 CSS
    inject_css("workspace")

    # target="_self" 表示当前页跳转
    logo_b64 = _img_to_base64(os.path.join(_PUBLIC_DIR, "DocClaw.png"))
    if logo_b64:  
        st.sidebar.markdown(f"""
        <a class="sidebar-logo-link" href="?go=home" target="_self" title="返回首页">
            <img src="{logo_b64}" alt="DocClaw">
        </a>
        """, unsafe_allow_html=True)

    # --- 板块 1：创作 ---
    st.sidebar.markdown(
        '<div class="nav-section-title" style="border-top:none; margin-top:0;">创作</div>',
        unsafe_allow_html=True)
    _nav_button("快速开始", "nav_home", ":material/auto_awesome:", "home")

    # --- 板块 2：功能 ---
    st.sidebar.markdown('<div class="nav-section-title">功能</div>', unsafe_allow_html=True)
    for key, info in FUNC_PAGES.items():
        _nav_button(info["label"], f"nav_{key}", f":material/{info['icon']}:", key)

    # --- 板块 3：资源 ---
    st.sidebar.markdown('<div class="nav-section-title">资源</div>', unsafe_allow_html=True)
    for key, info in RESOURCE_PAGES.items():
        _nav_button(info["label"], f"nav_{key}", f":material/{info['icon']}:", key)

    # --- 底部版本号 ---
    st.sidebar.markdown('<div class="sidebar-version">v1.0 · DocClaw</div>',
                        unsafe_allow_html=True)


# ============================================================
# 3. 主工作区
# ============================================================

# 快速开始推荐语：点击后自动填入输入框
TRY_EXAMPLES = [
    "帮我拆解一个「面向独立开发者的 AI 笔记工具」的产品需求",
    "帮我调研一下 Notion AI、Craft.io、Coda 三款竞品的核心差异",
    "生成一份 v2.0 的 PRD，功能包含：AI 摘要 + 自动标签 + 双链笔记",
    "我们决定把向量库从 Pinecone 换成 Chroma，评估一下对现有 PRD 的影响",
    "帮我搜搜之前关于「为什么选 PostgreSQL 而不是 MySQL」的决策记录",
    "帮我把v1.0 的 PRD 保存到本地，并将 v2.0 的 PRD 同步到 Wiki 中",
]

# 模型下拉框选项（todo纯前端展示，接入后端后再改）
CHAT_MODELS = ["qwen3-max"]
EMBEDDING_MODELS = ["text-embedding-v3", "text-embedding-v4"]


def render_workspace():
    """工作区路由器：根据 session_state["page"] 决定渲染哪个页面
    单页路由模式：Streamlit 没有官方多页路由
    用一个状态变量 + if/else 分发即模拟多页
    """
    # .get(key, 默认值)：page 尚未初始化时返回 "home"
    page = st.session_state.get("page", "home")

    # 快速开始页
    if page == "home":
        _render_home()
        return

    # 联系我们页
    if page == "contact":
        _render_contact()
        return

    # 历史记录页
    if page == "history":
        _render_history()
        return

    # 需求拆解页
    if page == "idea":
        _render_idea()
        return

    # 其余页面：从查询表取标题信息，渲染标题 + 占位卡片
    info = ALL_PAGES[page]
    st.markdown(f'<h1 class="page-title">{info["label"]}</h1>',
                unsafe_allow_html=True)
    _placeholder_page(info["label"])


def _fill_input(example: str):
    """试试按钮回调：把推荐语填入输入框"""
    st.session_state["zooop_input"] = example  # 与 text_area 的 key 对应


# ---- 快速开始页 ----

def _render_home():
    """快速开始页"""
    # 三列布局，宽度比 1:3:1
    left, center, right = st.columns([1, 3, 1])

    # with 列对象：该缩进块内创建的组件都落在这列里
    with center:
        st.markdown("""
        <div class="zooop-home">
            <h1 class="zooop-title">嗨！今天有什么好点子？</h1>
            <p class="zooop-subtitle">一句话描述你的产品想法，哪怕是一个抽象且模糊的 idea ，DocClaw 都能帮你拆解、调研，最终生成让你满意的 PRD ！</p>
        </div>
        """, unsafe_allow_html=True)

        # --- 输入卡片：对话框 + 模型选择 + 生成按钮 ---
        # st.container(border=True)：带边框的分组容器，把相关组件
        # 视觉上包成一张"卡片"（样式由 styles.py 增强）
        with st.container(border=True):
            # 多行文本输入框。key="zooop_input" 使输入内容自动存入
            # session_state，重跑不丢失，其他地方可随时读取
            st.text_area(
                "输入你的产品想法",
                placeholder="例如：我想做一个面向独立开发者的 AI 笔记工具，核心功能是自动整理会议纪要...",
                height=120,                     # 输入框高度
                label_visibility="collapsed",   # 折叠标签文字
                key="zooop_input",
            )
            # 一行三列放：聊天模型 / 嵌入模型 / 生成按钮
            col_model, col_embed, col_gen = st.columns(3)   # 等宽三列
            with col_model:
                # key 与 _fill_input 回填机制同理：选择结果存 session_state
                st.selectbox("聊天模型", CHAT_MODELS, key="zooop_chat_model")
            with col_embed:
                st.selectbox("嵌入模型", EMBEDDING_MODELS, key="zooop_embed_model")
            with col_gen:
                st.markdown("<br>", unsafe_allow_html=True)
                generate = st.button("生成", type="primary", use_container_width=True,
                                     key="zooop_gen", icon=":material/auto_awesome:")

        # --- 生成按钮反馈 ---
        # generate 只在点击后的这一轮运行为 True，所以提示只显示
        # 一轮，下次任意交互（重跑）后自动消失——一次性反馈
        if generate:
            # 从 session_state 读取输入框内容并去首尾空白
            idea = st.session_state.get("zooop_input", "").strip()
            if not idea: 
                st.warning("请先输入你的产品想法")
            else:
                # todo调用生成接口
                st.info("目前已开发的功能：“需求拆解”、“历史记录”、“联系我们” ！")

        # --- 试试推荐语 ---
        st.markdown('<div class="zooop-try-label">试试：</div>', unsafe_allow_html=True)
        # range(0, len, 2)：步长 2，每次取 2 条作为一行
        # 6 条示例 → i = 0, 2, 4 共三行
        for i in range(0, len(TRY_EXAMPLES), 2):
            row_cols = st.columns(2)  # 每行两个等宽列
            # 切片 TRY_EXAMPLES[i:i+2] 取本行的 1~2 条；
            # enumerate 给出列下标 j（0 或 1），决定放进哪个列
            for j, example in enumerate(TRY_EXAMPLES[i:i + 2]):
                with row_cols[j]:
                    # on_click 回调 + args：点击时 Streamlit 会先执行
                    # _fill_input(example) 再重跑脚本（见 _fill_input 文档）
                    # key 里的 i/j 保证每个按钮的 key 全页唯一
                    st.button(example, key=f"try_{i}_{j}", use_container_width=True,
                              on_click=_fill_input, args=(example,))


# ---- 联系我们页 ----

GITHUB_URL = "https://github.com/thp322?tab=repositories"
DOUYIN_URL = "https://www.douyin.com/user/MS4wLjABAAAA_UNh4V6nLwF1AK5fJ6u3UnDHSD4hL0e-KNx6cy99oWA?from_tab_name=main"
_GITHUB_SVG = ('<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 .297c-6.63 0-12 5.373-12 12 '
               '0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724'
               '-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 '
               '1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76'
               '-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105'
               '-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552'
               ' 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 '
               '5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 '
               '22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/></svg>')
_DOUYIN_SVG = ('<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12.53.02C13.84 0 15.14.01 16.44 0c.08 '
               '1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26'
               '-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17'
               '-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18'
               '-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32'
               '-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 '
               '2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02'
               '-12.07z"/></svg>')
def _render_contact():
    """联系我们页"""
    st.markdown('<h1 class="page-title">联系我们</h1>', unsafe_allow_html=True)

    qr_b64 = _img_to_base64(os.path.join(_PUBLIC_DIR, "weixin.jpg"))
    qr_html = (f'<img class="contact-qr-img" src="{qr_b64}" alt="微信二维码">'
               if qr_b64 else '<div class="contact-qr-missing">二维码加载失败</div>')

    st.markdown(f"""
    <div class="contact-card">
        <p class="contact-name">Harper · 本项目的发起者和独立开发者</p>
        <p class="contact-bio">个人简介：一个游走在代码世界的编程爱好者。喜欢探索未知的事物，钻研新的技术，探寻未知的技术边界</p>
        <p class="contact-bio">如有技术问题或建议，欢迎与我联系！</p>
        <div class="contact-body">
            <div class="contact-qr">
                {qr_html}
            </div>
            <div class="contact-links">
                <a class="contact-link" href="{GITHUB_URL}" target="_blank" title="GitHub">{_GITHUB_SVG}</a>
                <a class="contact-link" href="{DOUYIN_URL}" target="_blank" title="抖音">{_DOUYIN_SVG}</a>
            </div>
        </div>
        <br>
        <p class="contact-bio">
            个人博客地址：<a href="https://harperlog.cn/" target="_blank">https://harperlog.cn/</a><br>
            其他作品集：<a href="https://harperwork.cn/" target="_blank">https://harperwork.cn/</a>
        </p>
    </div>
    """, unsafe_allow_html=True)


# ---- 历史记录页 ----

def _open_history(file_name: str):
    """「查看详情」按钮回调：记录选中的快照文件，rerun 后进入详情视图"""
    st.session_state["history_selected"] = file_name


def _back_history_list():
    """「返回列表」按钮回调"""
    st.session_state.pop("history_selected", None)


def _ask_delete_history(file_name: str):
    """「删除」按钮回调：进入该记录的二次确认态（不立即删除，防误触）"""
    st.session_state["history_pending_delete"] = file_name


def _cancel_delete_history():
    """取消删除"""
    st.session_state.pop("history_pending_delete", None)


def _confirm_delete_history(file_name: str):
    """确认删除：同时删除 history 快照与 chat_history 会话消息文件"""
    try:
        delete_conversation_record(file_name)
        st.toast("已删除该历史记录", icon="🗑️")
    except FileNotFoundError:
        st.toast("该记录已不存在", icon="⚠️")
    except OSError as exc:
        st.toast(f"删除失败：{exc}", icon="❌")
    finally:
        st.session_state.pop("history_pending_delete", None)
        # 若正在查看的正是被删记录，退回列表
        if st.session_state.get("history_selected") == file_name:
            st.session_state.pop("history_selected", None)


def _render_history():
    """历史记录页：列表视图 / 详情视图 二选一"""
    st.markdown('<h1 class="page-title">历史记录</h1>', unsafe_allow_html=True)

    if st.session_state.get("history_selected"):
        _render_history_detail(st.session_state["history_selected"])
    else:
        _render_history_list()


def _render_history_list():
    """历史列表：按时间倒序展示会话卡片"""
    records = list_conversation_records()

    st.markdown(
        f'<p class="history-subtitle">共 {len(records)} 条对话记录</p>',
        unsafe_allow_html=True)

    if not records:
        st.markdown(
            '<div class="history-empty">暂无历史记录<br>'
            '<span>完成一次对话后，记录会自动归档到这里</span></div>',
            unsafe_allow_html=True)
        return

    pending_delete = st.session_state.get("history_pending_delete")

    for rec in records:
        # 每条记录一个原生带边框容器，左信息右操作按钮
        with st.container(border=True):
            info_col, view_col, del_col = st.columns(
                [4.6, 1.1, 1.1], gap="small", vertical_alignment="center")
            with info_col:
                rounds = max(rec["message_count"] // 2, 0)
                st.markdown(f"""
                <div class="history-item-head">
                    <span class="history-badge">{_html_escape(rec["source"])}</span>
                    <span class="history-time">{_html_escape(rec["created_at"])} </span>
                    <span class="history-rounds">{rounds} 轮对话</span>
                </div>
                """, unsafe_allow_html=True)
                preview = rec["preview"] or "（无用户消息）"
                if len(preview) > 60:
                    preview = preview[:60] + "…"
                st.markdown(
                    f'<div class="history-preview">{_html_escape(preview)}</div>',
                    unsafe_allow_html=True)
            with view_col:
                st.button("查看详情",
                          key=f"open_{rec['file_name']}",
                          use_container_width=True,
                          on_click=_open_history,
                          args=(rec["file_name"],))
            with del_col:
                if pending_delete == rec["file_name"]:
                    # 二次确认态：红字提示 + 确认/取消，防止误删
                    st.caption('<span class="history-confirm-text">确认删除？</span>',
                               unsafe_allow_html=True)
                    st.button("确认删除",
                              key=f"confirm_{rec['file_name']}",
                              type="primary",
                              use_container_width=True,
                              on_click=_confirm_delete_history,
                              args=(rec["file_name"],))
                    st.button("取消",
                              key=f"cancel_{rec['file_name']}",
                              use_container_width=True,
                              on_click=_cancel_delete_history)
                else:
                    st.button("🗑 删除",
                              key=f"delete_{rec['file_name']}",
                              use_container_width=True,
                              on_click=_ask_delete_history,
                              args=(rec["file_name"],))


def _render_history_detail(file_name: str):
    """历史详情：功能来源 + 对话时间 + 完整对话记录（聊天气泡形式）"""
    try:
        record = load_conversation_record(file_name)
    except FileNotFoundError:
        st.error("该记录不存在或已被删除")
        st.session_state.pop("history_selected", None)
        return
    except Exception:
        st.error("该记录文件已损坏，无法读取")
        return

    st.button("← 返回列表", key="history_back", on_click=_back_history_list)

    st.markdown(f"""
    <div class="history-detail-meta">
        <div class="history-detail-title">
            <span class="history-badge">{_html_escape(record.get("source", "未知来源"))}</span>
            对话详情
        </div>
        <div class="history-detail-info">
            对话时间：{_html_escape(record.get("created_at", "未知"))}
            　|　🆔 会话 ID：{_html_escape(record.get("session_id", "未知"))}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 快照里 role 为标准 user/assistant，可直接喂给 st.chat_message；
    # .write() 会把含【DESC】的文本及 Markdown 正常渲染
    for msg in record.get("messages", []):
        role = msg.get("role", "assistant")
        if role not in ("user", "assistant"):
            role = "assistant"
        st.chat_message(role).write(msg.get("content", ""))


# ---- 需求拆解页 ----

def _render_idea():
    """需求拆解页"""
    st.markdown('<h1 class="page-title">需求拆解</h1>', unsafe_allow_html=True)

    if "message" not in st.session_state:
        st.session_state["message"] = [{"role": "assistant", "content": "请输入您对于产品模糊的idea，我会以【QUESTION】为开头反问您直至弄清您的想法，最后我会以【DESC】为开头为您输出初级的产品描述，随后为您详细地拆解产品需求！"}]

    if "rag" not in st.session_state:
        st.session_state["rag"] = IdeaRag()
        # 为本次浏览器会话分配唯一 session_id
        # todo接入登录后，可替换为 f"{user_id}_{conversation_id}" 
        st.session_state["session_id"] = uuid.uuid4().hex

    for message in st.session_state["message"]:
        st.chat_message(message["role"]).write(message["content"])


    # 在页面最下方提供用户输入栏
    prompt = st.chat_input()

    if prompt:
        # 在页面输出用户的提问
        st.chat_message("user").write(prompt)
        st.session_state["message"].append({"role": "user", "content": prompt})

        rag = st.session_state["rag"]
        session_config = {"configurable": {"session_id": st.session_state["session_id"]}}

        # ---- 阶段一：模糊 idea → 初级产品描述 ----
        with st.spinner("DocClaw 思考中..."):
            with st.chat_message("assistant"):
                desc_text = st.write_stream(rag.chat_stream(prompt, session_config))
        st.session_state["message"].append({"role": "assistant", "content": desc_text})

        # ---- 阶段二：输出带【DESC】前缀 → 初级产品描述已完成，自动衔接需求拆解 ----
        if desc_text.lstrip().startswith(DESC_PREFIX):
            with st.spinner("正在拆解产品需求..."):
                st.caption("已输出初级产品描述，需求拆解结果：")
                with st.chat_message("assistant"):
                    req_text = st.write_stream(rag.breakdown_stream(desc_text, session_config))
            st.session_state["message"].append({"role": "assistant", "content": req_text})


# ---- 占位页 ----

def _placeholder_page(title: str):
    """占位卡片：未开发功能页的统一占位展示"""
    st.markdown(f"""
    <div class="work-card">
        <div class="work-card-title">{title}</div>
        <p style="color:#6b7280;">功能开发中，敬请期待。</p>
    </div>
    """, unsafe_allow_html=True)





# ============================================================
# 4. 主入口
# ============================================================

def main():
    """应用入口：处理「返回首页」跳转 → 初始化状态 → 分发两种模式"""
    if st.query_params.get("go") == "home":
        st.query_params.clear()
        st.session_state["entered"] = False   # 回落地页
        st.session_state["page"] = "home"     # 工作页重置到首页

    # 保证"首次访问"有初始状态，且每次重跑不会覆盖用户已改的状态
    st.session_state.setdefault("entered", False)  # 是否已进入工作页
    st.session_state.setdefault("page", "home")    # 工作页当前页签

    # 模式分发：已进入 → 侧边栏 + 工作区；否则 → 落地页
    if st.session_state["entered"]:
        render_sidebar()
        render_workspace()
    else:
        render_landing()


if __name__ == "__main__":
    main()
