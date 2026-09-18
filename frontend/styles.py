"""
全局样式注入

通过 st.markdown(unsafe_allow_html=True) 注入 CSS，两套布局模式：
  - 落地页（landing）：隐藏侧边栏、内容居中、大标题 + 特性卡片
  - 工作页（workspace）：固定左侧侧边栏、wide 布局、卡片式工作区
"""


# 1. 落地页 CSS

LANDING_CSS = """
<style>
/* 落地页不渲染任何侧边栏内容：整个侧边栏容器、顶栏（含移动端的
   侧边栏展开按钮 stExpandSidebarButton）都隐藏，避免出现空抽屉入口 */
[data-testid="stSidebar"],
[data-testid="stHeader"],
footer,
button[kind="secondary"][data-testid="baseButton-secondary"] {
    display: none !important;
}

.stApp {
    background: #f7f9fd !important;
}

.block-container {
    max-width: 1000px !important;
    padding-top: 90px !important;
    padding-bottom: 80px !important;
}

.hero-title {
    font-size: 4rem !important;
    font-weight: 800 !important;
    color: #0d1f4b !important;
    text-align: center !important;
    line-height: 1.15 !important;
    letter-spacing: -0.02em !important;
    margin-bottom: 1.5rem !important;
}

.hero-subtitle {
    font-size: 1.2rem !important;
    color: #5c6b85 !important;
    text-align: center !important;
    line-height: 1.7 !important;
    margin-bottom: 3rem !important;
}

[data-testid="stElementContainer"]:has(.stButton) {
    width: 100% !important;
}

.stButton,
.stButton > div {
    display: flex !important;
    justify-content: center !important;
    width: 100% !important;
    text-align: center !important;
}

.stButton > button[kind="primary"] {
    background: #2563eb !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    padding: 0.7rem 2.6rem !important;
    margin-left: auto !important;
    margin-right: auto !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.25) !important;
    transition: all 0.2s ease !important;
}

.stButton > button[kind="primary"]:hover {
    background: #1d4ed8 !important;
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.32) !important;
    transform: translateY(-1px) !important;
}

.feature-grid {
    display: grid !important;
    grid-template-columns: repeat(3, 1fr) !important;
    gap: 1.25rem !important;
    margin-top: 3.5rem !important;
}

.feature-card {
    background: #ffffff !important;
    border: 1px solid #e4eaf4 !important;
    border-radius: 14px !important;
    padding: 1.6rem !important;
    transition: all 0.2s ease !important;
}

.feature-card:hover {
    border-color: #2563eb !important;
    box-shadow: 0 8px 24px rgba(37, 99, 235, 0.10) !important;
    transform: translateY(-3px) !important;
}

.feature-icon {
    width: 44px !important;
    height: 44px !important;
    border-radius: 10px !important;
    background: #e9f1fe !important;
    color: #2563eb !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin-bottom: 1rem !important;
}

.feature-icon svg {
    width: 22px !important;
    height: 22px !important;
}

.feature-title {
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    color: #13203c !important;
    margin-bottom: 0.45rem !important;
}

.feature-desc {
    font-size: 0.88rem !important;
    color: #64748b !important;
    line-height: 1.55 !important;
}

.footer-text {
    text-align: center !important;
    color: #9aa7bd !important;
    font-size: 0.85rem !important;
    margin-top: 4rem !important;
}

@media (max-width: 900px) {
    .feature-grid {
        grid-template-columns: 1fr !important;
    }
    .hero-title {
        font-size: 2.4rem !important;
    }
}
</style>
"""


# 2. 工作页 CSS

WORKSPACE_CSS = """
<style>
.hero-title,
.hero-subtitle,
.feature-grid,
.feature-card,
.feature-icon,
.footer-text {
    display: none !important;
}

[data-testid="stSidebar"] {
    background: #f8f9fc !important;
    border-right: 1px solid #e5e7eb !important;
}

[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    padding: 0 !important;
}

/* 桌面端（≥769px）：侧边栏固定 240px 常驻，隐藏原生折叠按钮
   （导航互跳走侧边栏按钮，回首页走 Logo） */
@media (min-width: 769px) {
    [data-testid="stSidebar"] {
        width: 240px !important;
        min-width: 240px !important;
        max-width: 240px !important;
        height: 100vh !important;
        transform: none !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        width: 240px !important;
        min-width: 240px !important;
    }

    [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        height: 100vh !important;
        padding: 0 0.9rem 1rem 0.9rem !important;
        position: relative !important;
    }

    [data-testid="stSidebarHeader"],
    [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }
}

/* 移动端（≤768px）：保留 Streamlit 原生抽屉（默认折叠、遮罩、滑入动画），
   不强制宽度和 transform；只统一内边距，并保留抽屉内的原生关闭按钮 */
@media (max-width: 768px) {
    [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        padding: 0 0.9rem 1rem 0.9rem !important;
    }

    [data-testid="stSidebarHeader"] {
        height: auto !important;
        padding: 0.7rem 0.2rem 0 0 !important;
    }

    [data-testid="stSidebarCollapseButton"] button {
        color: #4f46e5 !important;
    }

    /* 版本号：桌面端是 fixed 贴底（宽度随 240px 侧栏）；
       移动端抽屉宽度不固定，改为文档流内的普通块，避免相对视口错位 */
    .sidebar-version {
        position: static !important;
        width: auto !important;
        margin-top: 2rem !important;
    }

    /* 折叠状态下左上角的「展开侧边栏」唤起按钮（Streamlit 1.63 的
       testid 为 stExpandSidebarButton，位于顶部 stToolbar 内）：
       做成醒目的 44px 品牌色圆角按钮 */
    [data-testid="stExpandSidebarButton"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 44px !important;
        height: 44px !important;
        border-radius: 12px !important;
        background: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        box-shadow: 0 4px 14px rgba(13, 31, 75, 0.14) !important;
    }

    [data-testid="stExpandSidebarButton"] svg {
        color: #4f46e5 !important;
        width: 24px !important;
        height: 24px !important;
    }
}

[data-testid="stHeader"] {
    background: transparent !important;
}

/* 桌面端隐藏整个顶栏工具区（含展开按钮，桌面端侧栏常驻用不到）；
   移动端在上面的媒体查询里保留显示，否则无法唤起侧边栏 */
@media (min-width: 769px) {
    footer,
    .stDeployButton,
    .stAppToolbar {
        display: none !important;
    }
}

.stApp {
    background: #ffffff !important;
}

.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1400px !important;
}

.sidebar-logo-link {
    display: block !important;
    width: 120px !important;
    margin: 1.6rem auto 1.2rem auto !important;
    line-height: 0 !important;
    transition: opacity 0.2s !important;
}

.sidebar-logo-link:hover {
    opacity: 0.85 !important;
}

.sidebar-logo-link img {
    width: 120px !important;
    display: block !important;
}

.sidebar-version {
    position: fixed !important;
    bottom: 0.75rem !important;
    left: 0 !important;
    width: 240px !important;
    text-align: center !important;
    font-size: 0.72rem !important;
    color: #9ca3af !important;
    pointer-events: none !important;
    z-index: 10 !important;
}

[data-testid="stSidebar"] .stButton > button {
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    padding: 0.55rem 0.75rem !important;
    border-radius: 8px !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    color: #374151 !important;
    background: transparent !important;
    border: none !important;
    transition: all 0.15s ease !important;
    height: auto !important;
    min-height: 0 !important;
    line-height: 1.4 !important;
    width: 100% !important;
    text-align: left !important;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: #eef0ff !important;
    color: #667eea !important;
}

.nav-section-title {
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    color: #9ca3af !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    padding: 0.6rem 0.5rem 0.4rem 0.5rem !important;
    margin-top: 0.6rem !important;
    border-top: 1px solid #eceef3 !important;
}

.work-card {
    background: white !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 12px !important;
    padding: 1.5rem !important;
    margin-bottom: 1rem !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
}

.work-card-title {
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    color: #111827 !important;
    margin-bottom: 0.8rem !important;
}

.page-title {
    font-size: 2rem !important;
    font-weight: 700 !important;
    color: #111827 !important;
    margin-bottom: 0.3rem !important;
}

.zooop-home {
    text-align: center !important;
    padding: 3rem 0 1.5rem 0 !important;
}

.zooop-title {
    font-size: 2.75rem !important;
    font-weight: 700 !important;
    color: #111827 !important;
    margin: 0 0 0.75rem 0 !important;
    letter-spacing: -0.02em !important;
    line-height: 1.25 !important;
}

.zooop-subtitle {
    font-size: 1.05rem !important;
    color: #6b7280 !important;
    margin: 0 !important;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background: white !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06) !important;
    padding: 1rem 1.25rem !important;
}

[data-testid="stVerticalBlockBorderWrapper"] .stTextArea textarea {
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
    padding: 0.25rem !important;
    font-size: 1rem !important;
    resize: none !important;
}

[data-testid="stVerticalBlockBorderWrapper"] .stTextArea textarea:focus {
    border: none !important;
    box-shadow: none !important;
}

[data-testid="stVerticalBlockBorderWrapper"] .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    height: 38px !important;
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.35) !important;
    transition: all 0.2s ease !important;
}

[data-testid="stVerticalBlockBorderWrapper"] .stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(102, 126, 234, 0.5) !important;
}

.zooop-try-label {
    font-size: 0.82rem !important;
    color: #9ca3af !important;
    margin-top: 2rem !important;
    margin-bottom: 0.75rem !important;
    font-weight: 500 !important;
}

.stButton > button {
    border-radius: 14px !important;
    padding: 0.5rem 0.9rem !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    color: #6b7280 !important;
    background: #f3f4f6 !important;
    border: 1px solid #e5e7eb !important;
    transition: all 0.15s ease !important;
    min-height: 34px !important;
    height: auto !important;
    white-space: normal !important;
    text-align: left !important;
    line-height: 1.5 !important;
}

.stButton > button p {
    white-space: normal !important;
    word-break: break-word !important;
}

.stButton > button:hover {
    color: #4f46e5 !important;
    background: #eef0ff !important;
    border-color: #c7d2fe !important;
}

/* ---- 联系我们页 ---- */

.contact-card {
    background: #ffffff !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.05) !important;
    padding: 2rem 2.5rem !important;
    max-width: 780px !important;
    margin: 1.5rem auto 0 auto !important;
}

.contact-name {
    font-size: 1.15rem !important;
    font-weight: 600 !important;
    color: #111827 !important;
    margin: 0 0 0.5rem 0 !important;
}

.contact-bio {
    font-size: 0.95rem !important;
    color: #6b7280 !important;
    line-height: 1.75 !important;
    margin: 0 0 2rem 0 !important;
}

.contact-body {
    display: flex !important;
    align-items: flex-start !important;
    justify-content: center !important;
    gap: 4rem !important;
    flex-wrap: wrap !important;
}

.contact-qr {
    text-align: center !important;
}

.contact-qr-img {
    display: block !important;
    width: 240px !important;
    height: 240px !important;
    object-fit: cover !important;
    border-radius: 12px !important;
    border: 1px solid #e5e7eb !important;
}

.contact-qr-missing {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 240px !important;
    height: 240px !important;
    border: 1px dashed #d1d5db !important;
    border-radius: 12px !important;
    color: #9ca3af !important;
    font-size: 0.9rem !important;
}

.contact-qr-tip {
    font-size: 0.85rem !important;
    color: #9ca3af !important;
    margin: 0.75rem 0 0 0 !important;
}

.contact-links {
    display: flex !important;
    gap: 1rem !important;
    margin-top: 98px !important;
}

.contact-link {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 44px !important;
    height: 44px !important;
    border-radius: 50% !important;
    background: #f8f9fc !important;
    border: 1px solid #e5e7eb !important;
    color: #111827 !important;
    text-decoration: none !important;
    transition: all 0.2s ease !important;
}

.contact-link:hover {
    transform: translateY(-3px) !important;
    border-color: #111827 !important;
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12) !important;
}

.contact-link svg {
    width: 22px !important;
    height: 22px !important;
}

/* ---- 历史记录页 ---- */

.history-subtitle {
    color: #9ca3af !important;
    font-size: 0.9rem !important;
    margin: 0.25rem 0 1.25rem 0 !important;
}

/* 空状态卡片 */
.history-empty {
    max-width: 520px !important;
    margin: 3rem auto 0 auto !important;
    padding: 3rem 2rem !important;
    text-align: center !important;
    background: #ffffff !important;
    border: 1px dashed #d1d5db !important;
    border-radius: 16px !important;
    color: #6b7280 !important;
    font-size: 1.05rem !important;
    line-height: 2 !important;
}

.history-empty span {
    font-size: 0.85rem !important;
    color: #9ca3af !important;
}

/* 列表项头部：来源徽标 + 时间 + 轮数 */
.history-item-head {
    display: flex !important;
    align-items: center !important;
    flex-wrap: wrap !important;
    gap: 0.75rem !important;
    margin-bottom: 0.4rem !important;
}

.history-badge {
    display: inline-block !important;
    padding: 0.15rem 0.7rem !important;
    border-radius: 999px !important;
    background: #eef0ff !important;
    color: #4f46e5 !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
}

.history-time,
.history-rounds {
    font-size: 0.82rem !important;
    color: #9ca3af !important;
}

.history-model {
    font-size: 0.78rem !important;
    color: #6366f1 !important;
    background: #eef2ff !important;
    padding: 2px 10px !important;
    border-radius: 999px !important;
    font-family: ui-monospace, "Cascadia Code", Consolas, monospace !important;
}

.history-preview {
    color: #4b5563 !important;
    font-size: 0.92rem !important;
    line-height: 1.6 !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
}

/* 删除按钮：仅作用于历史卡片最后一列、且非二次确认态的次级按钮 */
div[data-testid="stVerticalBlockBorderWrapper"]
[data-testid="stColumn"]:last-child:not(:has(.history-confirm-text))
button[data-testid="baseButton-secondary"] {
    color: #dc2626 !important;
    border-color: #fecaca !important;
    background: #ffffff !important;
}

div[data-testid="stVerticalBlockBorderWrapper"]
[data-testid="stColumn"]:last-child:not(:has(.history-confirm-text))
button[data-testid="baseButton-secondary"]:hover {
    color: #b91c1c !important;
    border-color: #fca5a5 !important;
    background: #fef2f2 !important;
}

.history-confirm-text {
    color: #dc2626 !important;
    font-weight: 600 !important;
}

/* 列表中的带边框容器：圆角 + 悬浮上浮，与整体卡片语言一致 */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 14px !important;
    transition: box-shadow 0.2s ease, transform 0.2s ease, border-color 0.2s ease !important;
}

div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #c7d2fe !important;
    box-shadow: 0 6px 20px rgba(79, 70, 229, 0.10) !important;
    transform: translateY(-2px) !important;
}

/* 详情页元信息卡片 */
.history-detail-meta {
    background: #ffffff !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 14px !important;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.05) !important;
    padding: 1.25rem 1.5rem !important;
    margin: 0.5rem 0 1.5rem 0 !important;
}

.history-detail-title {
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    color: #111827 !important;
    margin-bottom: 0.5rem !important;
    display: flex !important;
    align-items: center !important;
    gap: 0.6rem !important;
}

.history-detail-info {
    font-size: 0.85rem !important;
    color: #9ca3af !important;
}

@media (max-width: 900px) {
    .zooop-title {
        font-size: 2rem !important;
    }
    .contact-links {
        margin-top: 0 !important;
    }
}
</style>
"""


def inject_css(mode: str = "landing"):
    """注入对应模式的 CSS（mode: "landing" | "workspace"）"""
    import streamlit as st
    css = LANDING_CSS if mode == "landing" else WORKSPACE_CSS
    st.markdown(css, unsafe_allow_html=True)
