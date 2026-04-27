"""
ZenBlog 后端服务 v5.0
仅保留文章管理功能（文章/分类/星标 CRUD）
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
    description="ZenBlog 文章管理系统",
    version="5.0.0"
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
# ZenBlog 辅助函数
# ============================================================

def _load_json(path):
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text(encoding='utf-8'))
    return None


def _save_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def _load_index():
    """加载文章索引"""
    data = _load_json(DATA_DIR / 'index.json')
    if data is None:
        return {"articles": [], "categories": [], "stars": []}
    return data


def _save_index(data):
    _save_json(DATA_DIR / 'index.json', data)


def _load_content(idx: int):
    """加载文章内容"""
    batch_idx = idx // 100
    content_file = DATA_DIR / f'content_{batch_idx}.json'
    if not content_file.exists():
        return None
    data = _load_json(content_file)
    if data is None:
        return None
    return data.get(str(idx))


def _save_content(idx: int, content: str):
    """保存文章内容"""
    batch_idx = idx // 100
    content_file = DATA_DIR / f'content_{batch_idx}.json'
    if content_file.exists():
        data = _load_json(content_file) or {}
    else:
        data = {}
    data[str(idx)] = content
    _save_json(content_file, data)


def _get_next_article_id():
    index_data = _load_index()
    articles = index_data.get('articles', [])
    if not articles:
        return 1
    return max(a['idx'] for a in articles) + 1


# ============================================================
# ZenBlog API — 文章/分类/星标
# ============================================================

@app.get("/api/article")
async def blog_get_article(idx: int = None, category: str = None):
    """获取文章内容 GET /api/article?idx=123"""
    index_data = _load_index()

    if idx is not None:
        # 获取单篇文章
        content = _load_content(idx)
        if content is None:
            raise HTTPException(404, "Article not found")

        # 查找文章元数据
        article_meta = None
        for a in index_data.get('articles', []):
            if a['idx'] == idx:
                article_meta = a
                break

        return {"idx": idx, "content": content, "meta": article_meta}

    # 返回所有文章列表
    return index_data


@app.post("/api/article")
async def blog_save_article(data: dict):
    """保存文章 POST /api/article"""
    idx = data.get('idx')
    content = data.get('content', '')
    title = data.get('title', '')
    category = data.get('category', 'default')

    if idx is None:
        # 新建文章
        idx = _get_next_article_id()

    _save_content(idx, content)

    # 更新索引
    index_data = _load_index()
    existing = next((a for a in index_data.get('articles', []) if a['idx'] == idx), None)
    if existing:
        existing['title'] = title or existing['title']
        existing['category'] = category
        existing['updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    else:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_article = {
            "idx": idx,
            "title": title or f"未命名文章 {idx}",
            "category": category,
            "created": now,
            "updated": now,
        }
        index_data.setdefault('articles', []).append(new_article)

    _save_index(index_data)
    return {"status": "saved", "idx": idx}


@app.put("/api/article/rename")
async def blog_rename_article(data: dict):
    """重命名文章"""
    index_data = _load_index()
    for a in index_data.get('articles', []):
        if a['idx'] == data['idx']:
            a['title'] = data['title']
            break
    _save_index(index_data)
    return {"status": "ok"}


@app.put("/api/article/move")
async def blog_move_article(data: dict):
    """移动文章到分类"""
    index_data = _load_index()
    for a in index_data.get('articles', []):
        if a['idx'] == data['idx']:
            a['category'] = data['category']
            break
    _save_index(index_data)
    return {"status": "ok"}


@app.put("/api/article/reorder")
async def blog_reorder_articles(data: dict):
    """重排文章顺序"""
    index_data = _load_index()
    order_map = {o['idx']: o['order'] for o in data.get('articles', [])}
    for a in index_data.get('articles', []):
        if a['idx'] in order_map:
            a['order'] = order_map[a['idx']]
    _save_index(index_data)
    return {"status": "ok"}


@app.delete("/api/article")
async def blog_delete_article(idx: int):
    """删除文章"""
    index_data = _load_index()
    index_data['articles'] = [a for a in index_data.get('articles', []) if a['idx'] != idx]
    _save_index(index_data)
    return {"status": "deleted"}


@app.get("/api/categories")
async def blog_get_categories():
    """获取分类列表"""
    return _load_index()


@app.post("/api/category/add")
async def blog_add_category(data: dict):
    """新增分类"""
    index_data = _load_index()
    if 'categories' not in index_data:
        index_data['categories'] = []
    cat = {
        "id": str(uuid.uuid4())[:8],
        "name": data.get('name', '新分类'),
        "order": len(index_data['categories'])
    }
    index_data['categories'].append(cat)
    _save_index(index_data)
    return cat


@app.put("/api/category/rename")
async def blog_rename_category(data: dict):
    """重命名分类"""
    index_data = _load_index()
    for c in index_data.get('categories', []):
        if c['id'] == data['id']:
            c['name'] = data['name']
            break
    _save_index(index_data)
    return {"status": "ok"}


@app.put("/api/category/reorder")
async def blog_reorder_categories(data: dict):
    """重排分类顺序"""
    index_data = _load_index()
    order_map = {o['id']: o['order'] for o in data.get('categories', [])}
    for c in index_data.get('categories', []):
        if c['id'] in order_map:
            c['order'] = order_map[c['id']]
    _save_index(index_data)
    return {"status": "ok"}


@app.delete("/api/category")
async def blog_delete_category(id: str):
    """删除分类"""
    index_data = _load_index()
    index_data['categories'] = [c for c in index_data.get('categories', []) if c['id'] != id]
    for a in index_data.get('articles', []):
        if a.get('category') == id:
            a['category'] = 'default'
    _save_index(index_data)
    return {"status": "deleted"}


@app.get("/api/stars")
async def blog_get_stars():
    """获取星标列表"""
    index_data = _load_index()
    return index_data.get('stars', [])


@app.post("/api/stars")
async def blog_save_stars(stars: list):
    """保存星标列表"""
    index_data = _load_index()
    index_data['stars'] = stars
    _save_index(index_data)
    return {"status": "ok"}


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
    return JSONResponse({"message": "Welcome to ZenBlog API v5.0"})


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
    print("   ZenBlog 后端服务 v5.0")
    print("   文章/分类/星标 管理")
    print("=" * 65)
    print("   访问地址:     http://localhost:8877")
    print("=" * 65)
    uvicorn.run(app, host="0.0.0.0", port=8877)
