from collections import defaultdict

def analyze_tokens(tokens, word_map, selected_levels):
    """
    统计 tokens 中每个等级的词频和出现顺序
    """
    level_count = defaultdict(int)
    level_words = defaultdict(list)

    for word, pos in tokens:
        pos_initial = pos[:1]
        if word not in word_map:
            continue

        info = word_map[word]
        if "level" not in info:
            continue
        level = info["level"]

        if level not in selected_levels:
            continue

        if "pos_map" not in info:
            # 不考虑词性
            level_count[level] += 1
            level_words[level].append(word)
        else:
            if pos_initial in info["pos_map"]:
                level_count[level] += 1
                level_words[level].append(word)

    return level_count, level_words
