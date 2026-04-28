"""
ZenBlog 后端服务 v6.0
MySQL 数据库版本 — 替换 JSON 文件存储
统一端口 8877
"""

from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, date
import json
import os
import uuid
import pymysql
from pathlib import Path

# ── 清除代理环境变量（避免请求被系统代理拦截）─────────────────
for _k in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
           "ftp_proxy", "FTP_PROXY", "all_proxy", "ALL_PROXY",
           "no_proxy", "NO_PROXY"]:
    os.environ.pop(_k, None)

# ── 禁止 requests/urllib3 读取 macOS 系统代理，强制直连 ────────
import requests.utils
requests.utils.get_environ_proxies = lambda url, no_proxy=None: {}
import requests.sessions
requests.sessions.Session.trust_env = False

# ============================================================
# 路径配置
# ============================================================
SITE_DIR = Path(__file__).parent.resolve()
DATA_DIR = SITE_DIR / 'data'

DATA_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="ZenBlog API",
    description="ZenBlog 文章管理系统 (MySQL)",
    version="6.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# MySQL 连接管理
# ============================================================

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "zenblog",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}


def get_db():
    """获取数据库连接（上下文管理器）"""
    conn = pymysql.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()


def _query(sql: str, params: tuple = None) -> List[Dict]:
    """执行查询，返回结果列表"""
    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()
    finally:
        conn.close()


def _execute(sql: str, params: tuple = None) -> int:
    """执行写操作，返回受影响行数"""
    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            conn.commit()
            return cur.rowcount
    finally:
        conn.close()


def _execute_insert(sql: str, params: tuple = None) -> int:
    """执行 INSERT，返回 lastrowid"""
    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()


# ============================================================
# 数据访问层
# ============================================================

def _get_all_articles() -> List[Dict]:
    """获取所有文章"""
    return _query("SELECT * FROM articles ORDER BY article_order ASC, idx ASC")


def _get_article_by_idx(idx: int) -> Optional[Dict]:
    rows = _query("SELECT * FROM articles WHERE idx = %s", (idx,))
    return rows[0] if rows else None


def _get_next_article_id() -> int:
    row = _query("SELECT MAX(idx) AS max_idx FROM articles")
    return (row[0]['max_idx'] or 0) + 1


def _get_categories() -> List[Dict]:
    return _query("SELECT * FROM categories ORDER BY cat_order ASC, id ASC")


def _get_cat_orders() -> Dict[str, List[int]]:
    """获取分类文章排序"""
    rows = _query("SELECT category, article_idx, sort_order FROM cat_orders ORDER BY sort_order ASC")
    result: Dict[str, List[int]] = {}
    for r in rows:
        cat = r['category']
        if cat not in result:
            result[cat] = []
        result[cat].append(r['article_idx'])
    return result


def _get_stars() -> List[int]:
    rows = _query("SELECT article_idx FROM stars ORDER BY article_idx ASC")
    return [r['article_idx'] for r in rows]


def _format_date(val):
    """将 date/datetime 或字符串格式化为 YYYY-MM-DD"""
    if val is None:
        return ''
    if hasattr(val, 'strftime'):
        return val.strftime('%Y-%m-%d')
    return str(val)[:10]


def _format_time(val):
    """将 time 或字符串格式化为 HH:MM"""
    if val is None:
        return ''
    s = str(val)
    return s[:5] if len(s) >= 5 else s


def _get_stock_lessons() -> Dict[str, Dict]:
    rows = _query("SELECT * FROM stock_lessons ORDER BY num ASC")
    result = {}
    for r in rows:
        result[str(r['num'])] = {
            "idx": r['article_idx'],
            "num": r['num'],
            "title": r['title'],
            "date": _format_date(r['lesson_date']),
            "time": _format_time(r['lesson_time']),
        }
    return result


def _build_index_response() -> Dict:
    """构建与旧版 index.json 结构一致的响应"""
    articles = _get_all_articles()
    categories_rows = _get_categories()
    cat_orders = _get_cat_orders()
    stars = _get_stars()
    stock_lessons = _get_stock_lessons()

    # 格式化文章列表
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

    # 格式化分类（对象格式，兼容前端）
    categories_obj = {}
    for c in categories_rows:
        categories_obj[c['name']] = {
            "icon": c['icon'] or '📄',
            "order": c['cat_order'],
        }

    return {
        "articles": articles_out,
        "categories": categories_obj,
        "cat_orders": cat_orders,
        "stock_lessons": stock_lessons,
        "stars": stars,
    }


# ============================================================
# ZenBlog API — 文章/分类/星标
# ============================================================

@app.get("/api/article")
async def blog_get_article(idx: int = None, category: str = None):
    """获取文章内容 GET /api/article?idx=123"""
    if idx is not None:
        article = _get_article_by_idx(idx)
        if article is None:
            raise HTTPException(404, "Article not found")

        return {
            "idx": idx,
            "content": article['content'] or '',
            "meta": {
                "idx": article['idx'],
                "title": article['title'],
                "date": _format_date(article['date']),
                "time": _format_time(article['time']),
                "category": article['category'],
                "preview": article['preview'] or '',
                "stock_num": article['stock_num'],
                "has_images": bool(article['has_images']),
                "images": json.loads(article['images']) if article['images'] else [],
            }
        }

    # 返回完整索引
    return _build_index_response()


@app.post("/api/article")
async def blog_save_article(data: dict):
    """保存文章 POST /api/article"""
    idx = data.get('idx')
    content = data.get('content', '')
    title = data.get('title', '')
    category = data.get('category', 'default')
    now = datetime.now()

    if idx is None:
        # 新建文章
        idx = _get_next_article_id()
        preview = (content[:200] + '...') if len(content) > 200 else content
        _execute_insert(
            "INSERT INTO articles (idx, title, category, preview, content, date, time, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (idx, title or f"未命名文章 {idx}", category, preview, content,
             now.date(), now.time(), now, now)
        )
    else:
        # 更新已有文章
        existing = _get_article_by_idx(idx)
        if existing:
            new_title = title or existing['title']
            new_category = category or existing['category']
            new_content = content or existing['content']
            preview = (new_content[:200] + '...') if len(new_content) > 200 else new_content
            _execute(
                "UPDATE articles SET title=%s, category=%s, preview=%s, content=%s, updated_at=%s WHERE idx=%s",
                (new_title, new_category, preview, new_content, now, idx)
            )
        else:
            preview = (content[:200] + '...') if len(content) > 200 else content
            _execute_insert(
                "INSERT INTO articles (idx, title, category, preview, content, date, time, created_at, updated_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (idx, title or f"未命名文章 {idx}", category, preview, content,
                 now.date(), now.time(), now, now)
            )

    return {"status": "saved", "idx": idx}


@app.put("/api/article/rename")
async def blog_rename_article(data: dict):
    """重命名文章"""
    _execute("UPDATE articles SET title=%s, updated_at=%s WHERE idx=%s",
             (data['title'], datetime.now(), data['idx']))
    return {"status": "ok"}


@app.put("/api/article/move")
async def blog_move_article(data: dict):
    """移动文章到分类"""
    _execute("UPDATE articles SET category=%s, updated_at=%s WHERE idx=%s",
             (data['category'], datetime.now(), data['idx']))
    return {"status": "ok"}


@app.put("/api/article/reorder")
async def blog_reorder_articles(data: dict):
    """重排文章顺序"""
    now = datetime.now()
    for item in data.get('articles', []):
        _execute("UPDATE articles SET article_order=%s, updated_at=%s WHERE idx=%s",
                 (item['order'], now, item['idx']))
    return {"status": "ok"}


@app.delete("/api/article")
async def blog_delete_article(idx: int):
    """删除文章"""
    _execute("DELETE FROM articles WHERE idx = %s", (idx,))
    _execute("DELETE FROM cat_orders WHERE article_idx = %s", (idx,))
    _execute("DELETE FROM stars WHERE article_idx = %s", (idx,))
    return {"status": "deleted"}


@app.get("/api/categories")
async def blog_get_categories():
    """获取分类列表（返回完整索引，前端依赖 categories 对象）"""
    return _build_index_response()


@app.post("/api/category/add")
async def blog_add_category(data: dict):
    """新增分类"""
    name = data.get('name', '新分类')
    # 检查是否已存在
    existing = _query("SELECT id FROM categories WHERE name = %s", (name,))
    if existing:
        return {"id": existing[0]['id'], "name": name, "order": 0}

    max_order = _query("SELECT MAX(cat_order) AS max_o FROM categories")
    new_order = (max_order[0]['max_o'] or -1) + 1
    cat_id = str(uuid.uuid4())[:8]
    _execute_insert(
        "INSERT INTO categories (id, name, cat_order) VALUES (%s, %s, %s)",
        (cat_id, name, new_order)
    )
    return {"id": cat_id, "name": name, "order": new_order}


@app.put("/api/category/rename")
async def blog_rename_category(data: dict):
    """重命名分类"""
    old_name = data.get('old_name') or data.get('id', '')
    new_name = data.get('new_name') or data.get('name', '')

    if not old_name or not new_name:
        raise HTTPException(400, "old_name and new_name required")

    # 更新 categories 表
    _execute("UPDATE categories SET name=%s WHERE name=%s", (new_name, old_name))
    # 更新 articles 表中所有引用该分类的文章
    _execute("UPDATE articles SET category=%s WHERE category=%s", (new_name, old_name))
    # 更新 cat_orders
    _execute("UPDATE cat_orders SET category=%s WHERE category=%s", (new_name, old_name))
    return {"status": "ok"}


@app.put("/api/category/reorder")
async def blog_reorder_categories(data: dict):
    """重排分类顺序"""
    # 前端传 order: [catName1, catName2, ...]
    order_list = data.get('order', data.get('categories', []))
    for i, name in enumerate(order_list):
        _execute("UPDATE categories SET cat_order=%s WHERE name=%s", (i, name))
    return {"status": "ok"}


@app.delete("/api/category")
async def blog_delete_category(name: str = Query(...), move_to: str = Query('default')):
    """删除分类"""
    _execute("DELETE FROM categories WHERE name = %s", (name,))
    _execute("UPDATE articles SET category=%s WHERE category=%s", (move_to, name))
    _execute("DELETE FROM cat_orders WHERE category = %s", (name,))
    return {"status": "deleted"}


@app.get("/api/stars")
async def blog_get_stars():
    """获取星标列表"""
    stars = _get_stars()
    return {"starred_idxs": stars}


@app.post("/api/stars")
async def blog_save_stars(data: dict):
    """保存星标列表"""
    # data 可以是 {"starred_idxs": [1,2,3]} 或直接是列表
    if isinstance(data, list):
        idxs = data
    elif isinstance(data, dict):
        idxs = data.get('starred_idxs', data.get('stars', []))
    else:
        idxs = []

    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM stars")
            for idx in idxs:
                cur.execute("INSERT INTO stars (article_idx) VALUES (%s)", (idx,))
            conn.commit()
    finally:
        conn.close()

    return {"status": "ok"}


# ============================================================
# 数据迁移接口（从 JSON 导入 MySQL）
# ============================================================

@app.post("/api/migrate")
async def blog_migrate_data():
    """从 data/index.json 和 data/content_*.json 导入数据到 MySQL"""
    import json as json_lib

    # 1. 加载 index.json
    index_path = DATA_DIR / 'index.json'
    if not index_path.exists():
        raise HTTPException(400, "data/index.json not found")

    index_data = json_lib.loads(index_path.read_text(encoding='utf-8'))
    articles = index_data.get('articles', [])
    categories = index_data.get('categories', {})
    cat_orders = index_data.get('cat_orders', {})
    stock_lessons = index_data.get('stock_lessons', {})
    stars = index_data.get('stars', [])

    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            # 清空旧数据
            cur.execute("DELETE FROM articles")
            cur.execute("DELETE FROM categories")
            cur.execute("DELETE FROM cat_orders")
            cur.execute("DELETE FROM stars")
            cur.execute("DELETE FROM stock_lessons")

            # 导入分类
            for cat_name, cat_info in categories.items():
                icon = cat_info.get('icon', '📄')
                cat_order = cat_info.get('order', 999)
                cur.execute(
                    "INSERT INTO categories (name, icon, cat_order) VALUES (%s, %s, %s)",
                    (cat_name, icon, cat_order)
                )

            # 导入文章
            for a in articles:
                idx = a['idx']
                title = a.get('title', '')
                date_str = a.get('date', '')
                time_str = a.get('time', '')
                category = a.get('category', 'default')
                preview = a.get('preview', '')
                stock_num = a.get('stock_num')
                has_images = 1 if a.get('has_images') else 0
                images = json_lib.dumps(a.get('images', []), ensure_ascii=False)
                article_order = a.get('order', 0)

                # 尝试从 content_*.json 加载内容
                batch_idx = idx // 100
                content_file = DATA_DIR / f'content_{batch_idx}.json'
                content = ''
                if content_file.exists():
                    content_data = json_lib.loads(content_file.read_text(encoding='utf-8'))
                    content = content_data.get(str(idx), '')

                # 处理空日期/时间
                date_val = date_str if date_str else None
                time_val = time_str if time_str else None

                cur.execute(
                    "INSERT INTO articles (idx, title, date, time, category, preview, stock_num, has_images, images, content, article_order) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (idx, title, date_val, time_val, category, preview,
                     stock_num, has_images, images, content, article_order)
                )

            # 导入 cat_orders
            for cat_name, idx_list in cat_orders.items():
                for sort_order, article_idx in enumerate(idx_list):
                    cur.execute(
                        "INSERT INTO cat_orders (category, article_idx, sort_order) VALUES (%s, %s, %s)",
                        (cat_name, article_idx, sort_order)
                    )

            # 导入 stock_lessons
            for num_str, lesson in stock_lessons.items():
                lesson_date = lesson.get('date', '')
                lesson_time = lesson.get('time', '')
                cur.execute(
                    "INSERT INTO stock_lessons (num, article_idx, title, lesson_date, lesson_time) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (lesson['num'], lesson['idx'], lesson['title'],
                     lesson_date if lesson_date else None,
                     lesson_time if lesson_time else None)
                )

            # 导入 stars
            if isinstance(stars, list):
                for idx in stars:
                    if isinstance(idx, (int, float)):
                        cur.execute("INSERT INTO stars (article_idx) VALUES (%s)", (int(idx),))

            conn.commit()
    finally:
        conn.close()

    return {
        "status": "migrated",
        "articles_count": len(articles),
        "categories_count": len(categories),
        "cat_orders_count": sum(len(v) for v in cat_orders.values()),
        "stock_lessons_count": len(stock_lessons),
        "stars_count": len(stars) if isinstance(stars, list) else 0,
    }


# ============================================================
# 静态文件服务
# ============================================================

app.mount("/images", StaticFiles(directory=str(SITE_DIR / "images")), name="images")


@app.get("/")
async def serve_homepage():
    """返回首页 HTML"""
    index_path = SITE_DIR / 'index.html'
    if index_path.exists():
        return FileResponse(
            str(index_path),
            media_type='text/html',
            headers={'Cache-Control': 'no-cache, no-store, must-revalidate', 'Pragma': 'no-cache', 'Expires': '0'}
        )
    return JSONResponse({"message": "Welcome to ZenBlog API v6.0"})


@app.get("/{path:path}")
async def serve_static(path: str):
    """静态资源兜底"""
    file_path = SITE_DIR / path
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))
    # SPA fallback：未匹配路径返回首页
    return FileResponse(
        str(SITE_DIR / 'index.html'),
        media_type='text/html',
        headers={'Cache-Control': 'no-cache, no-store, must-revalidate', 'Pragma': 'no-cache', 'Expires': '0'}
    )


if __name__ == "__main__":
    import uvicorn
    print("=" * 65)
    print("   ZenBlog 后端服务 v6.0 (MySQL)")
    print("   文章/分类/星标 管理")
    print("=" * 65)
    print("   访问地址:     http://localhost:8877")
    print("=" * 65)
    uvicorn.run(app, host="0.0.0.0", port=8877)
