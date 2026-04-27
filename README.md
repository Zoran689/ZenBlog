# ZenBlog

一个精美的缠中说禅博客文集系统 ，提供Mac和Windows安装包下载

![Python 3.14+](https://img.shields.io/badge/Python-3.14+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ 特性

- 📝 **文章 CRUD** — 创建、编辑、删除、重命名文章
- 📂 **分类管理** — 自由分类，支持排序和重命名
- ⭐ **星标收藏** — 快速收藏重要文章
- 🔍 **全文搜索** — 侧栏实时搜索过滤
- 📄 **Markdown** — 原生 Markdown 编辑与预览
- 🖼️ **图片支持** — 文章配图展示与灯箱预览
- 📱 **响应式** — 桌面 / 平板 / 手机自适应
- ⚡ **轻量** — 后端仅 330 行，零外部依赖（除 FastAPI）

## 🏗️ 架构

```
ZenBlog/
├── zenblog_backend.py    # FastAPI 后端（16 个 API 路由）
├── index.html            # 单页应用前端
├── start.sh              # 启动脚本
├── stop.sh               # 停止脚本
├── logo.png              # 站点 Logo
├── data/                 # 文章数据（JSON 存储）
│   ├── index.json        #   文章索引 + 分类 + 元数据
│   ├── content_*.json    #   分批存储的文章内容
│   └── stars.json        #   星标列表
└── images/               # 博客图片资源
```

| 层   | 技术                                              |
| ---- | ------------------------------------------------- |
| 后端 | Python / FastAPI                                  |
| 前端 | 原生 HTML + CSS + JavaScript（无框架）            |
| 数据 | JSON 文件（无需数据库）                           |
| 编辑 | [marked.js](https://marked.js.org/) Markdown 渲染 |

## 🚀 快速开始

### 方式一：一键启动

```bash
chmod +x start.sh
./start.sh
# 打开 http://localhost:8877
```

### 方式二：手动启动

```bash
pip install fastapi uvicorn requests
python3 zenblog_backend.py
# 打开 http://localhost:8877
```

### 停止服务

```bash
./stop.sh
```

## 📡 API 接口

所有接口返回 JSON，基础路径 `http://localhost:8877/api`

### 文章

| 方法   | 路径                   | 说明             |
| ------ | ---------------------- | ---------------- |
| GET    | `/api/article`         | 获取文章列表     |
| GET    | `/api/article?idx=123` | 获取单篇文章内容 |
| POST   | `/api/article`         | 创建/保存文章    |
| PUT    | `/api/article/rename`  | 重命名文章       |
| PUT    | `/api/article/move`    | 移动到分类       |
| PUT    | `/api/article/reorder` | 调整排序         |
| DELETE | `/api/article?idx=123` | 删除文章         |

### 分类

| 方法   | 路径                    | 说明         |
| ------ | ----------------------- | ------------ |
| GET    | `/api/categories`       | 获取分类列表 |
| POST   | `/api/category/add`     | 新建分类     |
| PUT    | `/api/category/rename`  | 重命名分类   |
| PUT    | `/api/category/reorder` | 调整分类顺序 |
| DELETE | `/api/category?id=xxx`  | 删除分类     |

### 星标

| 方法 | 路径         | 说明         |
| ---- | ------------ | ------------ |
| GET  | `/api/stars` | 获取星标列表 |
| POST | `/api/stars` | 保存星标列表 |

## 🛠️ 技术细节

- **端口**：`8877`
- **数据存储**：本地 JSON 文件，按每 100 篇一批分文件存储（`content_0.json`, `content_1.json`, …）
- **无数据库依赖**：不依赖 MySQL / SQLite / Redis 等
- **CORS**：全开放，支持跨域访问
- **缓存控制**：HTML 响应强制 no-cache，确保前端始终最新

## 📝 使用说明

1. **新建文章** → 点击「➕ 新建文章」，填写标题、选择分类、输入 Markdown 内容
2. **编辑文章** → 在文章详情页点击「✏️ 编辑」，修改后「💾 保存」
3. **管理分类** → 侧栏点击「➕」新增，右键重命名或删除
4. **搜索** → 侧栏搜索框输入关键词实时过滤

## 📄 License

MIT License
