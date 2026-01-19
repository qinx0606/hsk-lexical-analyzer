import thulac

def segment_text(text, thu, pos_fix):
    """
    使用 THULAC 分词并修正词性
    返回 tokens: [(word, pos), ...]
    """
    text = text.replace("_", "/")  # THULAC 输出下划线转斜杠
    # 分词
    tokens_raw = thu.cut(text, text=False)
    tokens = [(w, p) for w, p in tokens_raw]

    # POS 修正
    tokens = [
        (w, pos_fix.get(w, p)) if w in pos_fix else (w, p)
        for w, p in tokens
    ]

    return tokens
