r"""
清理文章内容中的 Windows 本地路径引用（如 [C:\Users\...]）
同时清理 MySQL 数据库和 JSON 文件
"""
import re
import json
import os
import pymysql

# ── MySQL 配置 ──
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "zenblog",
    "charset": "utf8mb4",
}

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# 匹配 [C:\...] 或 [C:/...] 形式的 Windows 路径（包括各种扩展名）
# 这匹配以 [C:\ 或 [C:/ 开头，到 ] 结束的文本
WIN_PATH_PATTERN = re.compile(r'\[C:(?:\\|/)[^\]]*\]')

def clean_content(text: str) -> str:
    """删除文章内容中的 Windows 路径引用"""
    if not text:
        return text
    # 替换为空格，保留段落结构
    cleaned = WIN_PATH_PATTERN.sub('', text)
    # 清理多余的空行（将连续3个以上换行减少为2个）
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()

def clean_mysql():
    """清理 MySQL 中所有文章的 content 字段"""
    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            # 查找所有包含 Windows 路径的文章
            cur.execute(
                "SELECT idx, content FROM articles WHERE content LIKE '%C:\\\\\\\\%' OR content LIKE '%C:/%'"
            )
            rows = cur.fetchall()
            print(f"MySQL 中找到 {len(rows)} 篇包含 Windows 路径的文章")

            total_removed = 0
            for idx, content in rows:
                before = content
                after = clean_content(content)
                if before != after:
                    removed = len(WIN_PATH_PATTERN.findall(before))
                    total_removed += removed
                    cur.execute(
                        "UPDATE articles SET content=%s, preview=%s WHERE idx=%s",
                        (after, (after[:200] + '...') if len(after) > 200 else after, idx)
                    )
                    print(f"  文章 {idx}: 删除了 {removed} 个路径引用")
            conn.commit()
            print(f"MySQL 清理完成，共删除 {total_removed} 个路径引用")
    finally:
        conn.close()

def clean_json():
    """清理 JSON 文件中所有文章的 content"""
    total_removed = 0
    for fname in sorted(os.listdir(DATA_DIR)):
        if not fname.startswith('content_') or not fname.endswith('.json'):
            continue
        fpath = os.path.join(DATA_DIR, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        changed = False
        for article_id, content in data.items():
            cleaned = clean_content(content)
            if cleaned != content:
                removed = len(WIN_PATH_PATTERN.findall(content))
                total_removed += removed
                data[article_id] = cleaned
                changed = True
                print(f"  {fname} / 文章 {article_id}: 删除了 {removed} 个路径引用")

        if changed:
            with open(fpath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"  ✓ {fname} 已更新")

    print(f"\nJSON 文件清理完成，共删除 {total_removed} 个路径引用")

if __name__ == '__main__':
    print("=" * 50)
    print("开始清理文章中的 Windows 本地路径引用")
    print("=" * 50)

    print("\n【清理 MySQL 数据库】")
    clean_mysql()

    print("\n【清理 JSON 文件】")
    clean_json()

    print("\n" + "=" * 50)
    print("全部清理完成！")
    print("=" * 50)
