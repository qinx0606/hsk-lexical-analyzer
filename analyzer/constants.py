import json

YCT_JSON = "HSK_wordlist/word_level_dict/YCT_WORD_MAP.json"
NEW_HSK_JSON = "HSK_wordlist/word_level_dict/NEW_HSK_WORD_MAP.json"
OLD_HSK_JSON = "HSK_wordlist/word_level_dict/OLD_HSK_WORD_MAP.json"

def load_map(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# 词表
YCT_MAP = load_map(YCT_JSON)
NEW_HSK_MAP = load_map(NEW_HSK_JSON)
OLD_HSK_MAP = load_map(OLD_HSK_JSON)

# 等级顺序
LEVEL_COLUMNS = [
    "YCT1","YCT2","YCT3","YCT4",
    "NEW_HSK1","NEW_HSK2","NEW_HSK3","NEW_HSK4","NEW_HSK5","NEW_HSK6","NEW_HSK7_9",
    "OLD_HSK1","OLD_HSK2","OLD_HSK3","OLD_HSK4","OLD_HSK5","OLD_HSK6"
]

# POS 修正
def load_pos_fix(path):
    fix = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            word, pos = line.split()
            fix[word] = pos
    return fix
