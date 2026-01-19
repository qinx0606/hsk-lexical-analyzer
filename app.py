import streamlit as st
import pandas as pd
from analyzer import segment_text, constants
import thulac
import io
import zipfile
import math
from collections import Counter, defaultdict

# =====================================================
# THULAC → 中文词性映射（关键！）
# =====================================================
# =====================================================
# THULAC → 规范中文词性（唯一、稳定）
# =====================================================
POS_THULAC_TO_CN = {
    "n": "名",
    "v": "动",
    "a": "形",
    "d": "副",
    "r": "代",
    "q": "量",
    "m": "数",
    "p": "介",
    "u": "助",      # ⭐ 只保留一个
    "c": "连",
    "f": "方",
    "t": "时",
    "s": "处",
    "e": "叹",
    "y": "语",
    "o": "拟",
    "g": "语素",
}


# =====================================================
# 工具函数：统一词表规则为 list
# =====================================================
def ensure_rule_list(info):
    if isinstance(info, list):
        return info
    return [info]


# ===============================
# Streamlit 页面设置
# ===============================
# st.set_page_config(page_title="汉语词汇等级分析工具", layout="wide")
st.set_page_config(
    page_title="汉语词汇等级统计工具",
    layout="wide",   # 宽屏模式
    page_icon="📊"
)

# =====================================================
# Session State 初始化
# =====================================================
if "df" not in st.session_state:
    st.session_state.df = None

if "excel_bytes" not in st.session_state:
    st.session_state.excel_bytes = None

if "zip_bytes" not in st.session_state:
    st.session_state.zip_bytes = None

# =====================================================
# 页面标题
# =====================================================

# 用 CSS 限制 file_uploader 的列表高度
st.markdown(
    """
    <style>
    /* 限制 file_uploader 的高度为 200px，多余部分滚动 */
    div[data-baseweb="file-uploader"] > div:first-child {
        max-height: 200px;
        overflow-y: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# 居中标题
st.markdown(
    """
    <h1 style="text-align: center;">📊 汉语词汇等级自动统计工具</h1>
    <hr>
    """,
    unsafe_allow_html=True
)
# st.markdown("---")  # 分割线
# 简洁工具介绍
# ===============================
st.markdown("#### 🎯 工具介绍")
st.markdown(
    """
- 本工具支持批量上传 UTF-8 编码的 TXT 文本，可自动统计各文本中**新HSK（1-9级）**、**旧HSK（1-6级）**及**YCT 少儿汉语（1-4级）** 词汇等级的 **频数和词序列**。<br>
- 工具调用 **[THULAC](https://thulac.thunlp.org/)**  (*`THU Lexical Analyzer for Chinese，清华大学自然语言处理与社会人文计算实验室研制`*)  对中文文本进行分词，
分词后的文本可打包下载为 `segmented_texts.zip`，方便学习与研究。
"""
)

# 并排显示功能概览和适用场景
# col1_function, col2_usage = st.columns([3, 1])  # 宽度比例 3:1

st.markdown("#### ⚡ 功能概览")
st.markdown(
    """
1. <b>批量文本上传：</b> 支持同时上传多个 UTF-8 编码 TXT 文件。<br>
2. <b>自动中文分词：</b> 调用 <a href="https://thulac.thunlp.org/" target="_blank">**THULAC**</a> 进行高效分词。<br>
3. <b>词汇等级统计：</b> 根据所选词表（新HSK、旧HSK、YCT少儿汉语）自动统计对应等级的词频和词序列。<br>
4. <b>下载结果：</b><br>
&nbsp;&nbsp;&nbsp;&nbsp;- <code>词频统计（Excel）</code>：导出包含各等级词频和词序列的 Excel 文件。<br>
&nbsp;&nbsp;&nbsp;&nbsp;- <code>分词文本（ZIP）</code>：批量下载分词后的 TXT 文本，便于保存或二次分析。
""",
    unsafe_allow_html=True
)


st.markdown("---")  # 分割线


# ===============================
# 用户上传文本
# ===============================
st.markdown("#### 📂 上传文件")
uploaded_files = st.file_uploader(
    "上传一个或多个 TXT 文件", type=["txt"], accept_multiple_files=True
)
st.markdown("---")  # 分割线
st.markdown("### 🗂️ 选择词表并统计词频")
# ===============================
col1, col2, col3 = st.columns([2, 0.2, 1])
# ===============================
# 用户选择词表和等级
# ===============================
with col1:
    wordmap_options = {
        "新HSK等级词汇（1-9级）": constants.NEW_HSK_MAP,
        "旧HSK等级词汇（1-6级）": constants.OLD_HSK_MAP,
        "YCT少儿汉语（1-4级）": constants.YCT_MAP
    }

    selected_wordmap_name = st.selectbox("选择词表", list(wordmap_options.keys()))
    selected_wordmap = wordmap_options[selected_wordmap_name]
    # 自动获取该词表中所有等级
    # selected_levels = sorted({v["level"] for v in selected_wordmap.values()})
    # selected_levels = sorted({v["level"] for v in selected_wordmap.values() if "level" in v})
    selected_levels = sorted(
        {rule["level"] for info in selected_wordmap.values()
         for rule in ensure_rule_list(info)}
    )




    # ===============================
    # 统计按钮
    # ===============================
with col3:
    st.markdown(
    """
    <style>
    div.stButton > button:first-child {
        margin-top: 10px;  /* 向下移动 15px */
    }
    </style>
    """,
    unsafe_allow_html=True
)
    do_analysis = st.button("📊 统计词频")

# -------------------------------
# 点击按钮后执行统计
# -------------------------------
if do_analysis:
    if not uploaded_files:
        st.warning("请先上传至少一个 TXT 文件")
    else:
        # ===============================
        # 初始化 THULAC
        # ===============================
        thu = thulac.thulac(
            seg_only=False,
            user_dict="user_dict/user_dict.txt"
        )

        # 读取 POS 修正表
        pos_fix = constants.load_pos_fix("user_dict/pos_fix.txt")

        # ===============================
        # 分析上传文件
        # ===============================
        results = []
        segmented_files = {}  # 存储每个文件的分词文本

        if uploaded_files:
            for uploaded_file in uploaded_files:
                text = uploaded_file.read().decode("utf-8")

                # -------- 分词 + POS 修正 --------
                raw_tokens = segment_text(text, thu, pos_fix)
                # -------- 清理 tokens（去掉空词和空标注和标点符号） --------
                base_tokens = [(w.replace("\ufeff", "").strip(), p) for w, p in raw_tokens
                               if w and w.replace("\ufeff", "").strip() != "" and p != "w"]

                
                # -------- 保存分词文本供下载 --------
                segmented_text = " ".join([f"{w}/{p}" for w, p in raw_tokens if w.strip() != "" and p.strip() != ""])
                segmented_files[uploaded_file.name] = segmented_text
                
                

                # -------- 统计词频和序列 --------
                level_count = Counter()
                level_words = defaultdict(list)

                used_indices = set()  # ⭐ 关键：记录哪些 token 已被“吃掉”

                # ===============================
                # 核心：按词 + 多规则 + 词性匹配
                # ===============================
                for i, (w, p) in enumerate(base_tokens):
                    if w not in selected_wordmap:
                        continue

                    rules = ensure_rule_list(selected_wordmap[w])
                    p0 = p[0]   # ⭐ 只取 THULAC 词性首字母# 设计选择：将 THULAC 复合词性压缩为首字母
                    pos_cn = POS_THULAC_TO_CN.get(p0)

                    for rule in rules:
                        level = rule.get("level")
                        if level not in selected_levels:
                            continue

                        # 有 pos_map 才判断词性
                        if "pos_map" in rule:
                            if pos_cn is None or pos_cn not in rule["pos_map"]:
                                continue

                        # 命中规则
                        level_count[level] += 1
                        level_words[level].append(w)
                        used_indices.add(i)
                        break   # ⭐ 关键：只命中一条规则

                # -------- 统计非词表词汇（去掉标点） --------
                other_words = [
                    base_tokens[i][0]
                    for i in range(len(base_tokens))
                    if i not in used_indices
                ]

                other_freq = len(other_words)
                other_seq = ", ".join(other_words)

                # -------- 去掉标点统计总词数和不同词数 --------
                total_tokens = len(base_tokens)
                total_types = len({w for w, _ in base_tokens})

                type_token_ratio = total_types/math.sqrt(total_tokens) if total_tokens > 0 else 0

                if sum(level_count.values()) + other_freq != total_tokens:
                    st.error(
                        f"统计不一致：{sum(level_count.values())} + {other_freq} != {total_tokens}"
                    )
                    st.stop()

                                # -------- 生成 DataFrame 行 --------
                row = {
                    "文件名": uploaded_file.name
                }

                for lv in selected_levels:
                    row[f"{lv}_频数"] = level_count.get(lv, 0)
                    row[f"{lv}_词序列"] = ", ".join(level_words.get(lv, []))

                # 添加非词表统计
                row["不属于当前词表的词汇_频数"] = other_freq
                row["不属于当前词表的词汇_词序列"] = other_seq
                row["文本_总词数_Token"] = total_tokens
                row["文本_不同词数_Type"] = total_types
                row["词汇多样性"] = type_token_ratio
                results.append(row)

            
            # -------- 显示统计表 --------
            df = pd.DataFrame(results)
            st.session_state.df = df # 保存到 session_state



            # Excel
            # df 是要导出的 DataFrame
            excel_buf = io.BytesIO()  # 内存文件
            with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
                # 不需要 writer.save()，with 会自动保存
            # 重置指针
            excel_buf.seek(0)
            st.session_state.excel_bytes = excel_buf.getvalue()
            
            # -------- 打包分词文本为 zip 下载 --------
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for fname, content in segmented_files.items():
                    seg_name = fname.replace(".txt", "_seg.txt")
                    zf.writestr(seg_name, content)
            zip_buffer.seek(0)
            st.session_state.zip_bytes = zip_buffer.getvalue()

# =====================================================
# ⭐ 永久结果区（和按钮无关）
# =====================================================
if st.session_state.df is not None:
    st.markdown("#### 📈 统计结果")
    st.dataframe(
        st.session_state.df,
        height=200,
        use_container_width=True
    )




    st.markdown("#### 💾 下载结果")
    with st.expander("下载词频统计（Excel）、分词文本（ZIP）"):
        download_col1, download_col2 = st.columns([1, 1])
        download_col1.download_button(label="⬇️ 词频统计（Excel）",
        data = st.session_state.excel_bytes,
        file_name="词汇等级统计结果.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
        download_col2.download_button(label="⬇️ 分词文本（ZIP）",
        data = st.session_state.zip_bytes,
        file_name="segmented_texts.zip",
        mime="application/zip")


## 添加footer
st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f8f9fa;
        color: #555;
        text-align: center;
        padding: 5px 0;
        font-size: 0.85rem;
        border-top: 1px solid #ddd;
        z-index: 50;
    }

    /* 给页面底部留空间，避免内容被 footer 挡住 */
    .block-container {
        padding-bottom: 500px;
    }
    </style>

    <div class="footer">
    <br>Created by: Qin Xu (Kyoto University), Yu zhu (Xiamen University)
        <br>&copy; 汉语语词汇等级自动统计工具. All rights reserved.
        <br>Version 1.0 · First released on 2026-01-20</p>

        
    </div>
    """,
    unsafe_allow_html=True
)
