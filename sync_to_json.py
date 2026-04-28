#!/usr/bin/env python3
"""
ZenBlog MySQL → JSON 同步脚本
从 MySQL 导出所有数据到 data/index.json 和 data/content_*.json，
使 GitHub Pages 能获取最新数据。
"""

import json
import os
from pathlib import Path
import pymysql

# ── 路径 ──────────────────────────────────────────────
SITE_DIR = Path(__file__).parent.resolve()
DATA_DIR = SITE_DIR / 'data'

# ── MySQL 连接 ─────────────────────────────────────────
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "zenblog",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}


def _query(sql: str, params: tuple = None):
    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()
    finally:
        conn.close()


def _format_date(val):
    if val is None:
        return ''
    if hasattr(val, 'strftime'):
        return val.strftime('%Y-%m-%d')
    return str(val)[:10]


def _format_time(val):
    if val is None:
        return ''
    s = str(val)
    return s[:5] if len(s) >= 5 else s


def sync():
    print("📥 从 MySQL 读取数据...")

    # 1. 读取所有数据
    articles = _query("SELECT * FROM articles ORDER BY article_order ASC, idx ASC")
    categories = _query("SELECT * FROM categories ORDER BY cat_order ASC, id ASC")
    cat_orders_rows = _query("SELECT category, article_idx, sort_order FROM cat_orders ORDER BY sort_order ASC")
    stars_rows = _query("SELECT article_idx FROM stars ORDER BY article_idx ASC")
    stock_lessons_rows = _query("SELECT * FROM stock_lessons ORDER BY num ASC")

    # 2. 构建 index.json
    articles_out = []
    for a in articles:
        articles_out.append({
            "idx": a['idx'],
            "title": a['title'],
            "date": _format_date(a['date']),
            "time": _format_time(a['time']),
            "category": a['category'],
            "preview": a['preview'] or '',
            "stock_num": a['stock_num'],
            "has_images": bool(a['has_images']),
            "images": json.loads(a['images']) if a['images'] else [],
        })

    categories_obj = {}
    for c in categories:
        categories_obj[c['name']] = {
            "icon": c['icon'] or '📄',
            "order": c['cat_order'],
        }

    cat_orders_obj = {}
    for r in cat_orders_rows:
        cat = r['category']
        if cat not in cat_orders_obj:
            cat_orders_obj[cat] = []
        cat_orders_obj[cat].append(r['article_idx'])

    stars_list = [r['article_idx'] for r in stars_rows]

    stock_lessons_obj = {}
    for r in stock_lessons_rows:
        stock_lessons_obj[str(r['num'])] = {
            "idx": r['article_idx'],
            "num": r['num'],
            "title": r['title'],
            "date": _format_date(r['lesson_date']),
            "time": _format_time(r['lesson_time']),
        }

    index_data = {
        "articles": articles_out,
        "categories": categories_obj,
        "cat_orders": cat_orders_obj,
        "stock_lessons": stock_lessons_obj,
    }

    # 只有 stars 非空时才写入
    if stars_list:
        index_data["stars"] = stars_list

    print(f"   articles: {len(articles_out)}")
    print(f"   categories: {len(categories_obj)}")
    print(f"   cat_orders: {sum(len(v) for v in cat_orders_obj.values())}")
    print(f"   stock_lessons: {len(stock_lessons_obj)}")
    print(f"   stars: {len(stars_list)}")

    # 3. 写 index.json
    print("\n📝 写入 data/index.json...")
    (DATA_DIR / 'index.json').write_text(
        json.dumps(index_data, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    print("   ✅ 完成")

    # 4. 写 content_*.json（按 batch 分组）
    print("\n📝 写入 data/content_*.json...")
    content_batches = {}
    for a in articles:
        idx = a['idx']
        batch_key = idx // 100
        if batch_key not in content_batches:
            content_batches[batch_key] = {}
        content_batches[batch_key][str(idx)] = a['content'] or ''

    # 删除旧的 content 文件
    for f in DATA_DIR.glob("content_*.json"):
        f.unlink()

    # 写新文件
    for batch_key in sorted(content_batches.keys()):
        filepath = DATA_DIR / f'content_{batch_key}.json'
        filepath.write_text(
            json.dumps(content_batches[batch_key], ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        print(f"   content_{batch_key}.json: {len(content_batches[batch_key])} 篇文章")

    print(f"\n✅ 同步完成！共 {len(content_batches)} 个 content 文件")


if __name__ == "__main__":
    sync()
