# ZenBlog 🧘

禅意博客文章管理系统 — 缠中说禅博客全集阅读器。

[![GitHub Pages](https://img.shields.io/badge/ZenBlog-在线访问-00BFA5?style=flat-square)](https://Zoran689.github.io/ZenBlog/)
[![GitHub Release](https://img.shields.io/github/v/release/Zoran689/ZenBlog?style=flat-square&label=下载安装包)](https://github.com/Zoran689/ZenBlog/releases/latest)
![Python 3.14+](https://img.shields.io/badge/Python-3.14+-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green?style=flat-square)
![Electron](https://img.shields.io/badge/Electron-35+-9FEAF9?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## 🌐 在线访问 & 下载

| 方式 | 链接 | 说明 |
|------|------|------|
| 🌍 **在线版** | [**Zoran689.github.io/ZenBlog**](https://Zoran689.github.io/ZenBlog/) | GitHub Pages 托管，无需安装，浏览器直接打开 |
| 🍎 **macOS** | [ZenBlog-x.x.x-mac-arm64.dmg](https://github.com/Zoran689/ZenBlog/releases/latest) | Apple Silicon（M 系列芯片） |
| 🍎 **macOS** | [ZenBlog-x.x.x-mac-x64.dmg](https://github.com/Zoran689/ZenBlog/releases/latest) | Intel 芯片 |
| 🪟 **Windows** | [ZenBlog-x.x.x-win-x64.exe](https://github.com/Zoran689/ZenBlog/releases/latest) | Windows 10/11 x64 |
| 🐧 **Linux** | [ZenBlog-x.x.x-linux-x64.AppImage](https://github.com/Zoran689/ZenBlog/releases/latest) | 主流 Linux 发行版 |

> 所有安装包均通过 GitHub Actions 自动构建，发布在 [Releases 页面](https://github.com/Zoran689/ZenBlog/releases)。

---

## ✨ 特性

- 📝 **文章 CRUD** — 创建、编辑、删除、重命名文章
- 📂 **分类管理** — 自由分类，支持排序和重命名
- ⭐ **星标收藏** — 快速收藏重要文章
- 🔍 **全文搜索** — 侧栏实时搜索过滤
- 📄 **Markdown** — 原生 Markdown 编辑与预览
- 🖼️ **图片支持** — 文章配图展示与灯箱预览
- 📱 **响应式** — 桌面 / 平板 / 手机自适应
- ⚡ **轻量** — 后端仅 330 行核心代码
- 🖥️ **跨平台桌面应用** — macOS / Windows / Linux
- 📡 **GitHub Pages 部署** — 静态模式直接从 JSON 加载数据

---

## 🏗️ 架构

```
ZenBlog/
├── .github/workflows/
│   └── build-installers.yml    # GitHub Actions：自动构建安装包
├── electron/                    # Electron 主进程
│   ├── main.js                  #   主进程入口（启动后端 + 创建窗口）
│   ├── preload.js               #   预加载脚本
│   └── afterPack.js             #   打包后处理（macOS 签名）
├── zenblog_backend.py           # FastAPI 后端（16+ API 路由）
├── index.html                   # 单页应用前端（原生 HTML/CSS/JS）
├── start.sh / stop.sh           # 启动 / 停止脚本
├── build_python.sh              # PyInstaller 打包脚本
├── sync_to_json.py              # MySQL → JSON 同步脚本
├── package.json                 # Electron + electron-builder 配置
├── requirements.txt             # Python 依赖
├── data/                        # 文章数据
│   ├── index.json               #   文章索引 + 分类 + 元数据
│   └── content_*.json           #   分批存储的文章内容（每 100 篇一批）
└── images/                      # 博客图片资源
```

### 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | Python / FastAPI |
| 前端 | 原生 HTML + CSS + JavaScript（无框架） |
| 桌面 | Electron + electron-builder |
| 数据 | JSON 文件 / MySQL（可选） |
| 编辑 | [marked.js](https://marked.js.org/) Markdown 渲染 |
| CI/CD | GitHub Actions（自动构建 + 部署） |

### 部署模式

ZenBlog 支持三种运行模式：

| 模式 | 数据源 | 适用场景 |
|------|--------|----------|
| **GitHub Pages 静态** | `data/*.json` | 在线浏览，无需后端 |
| **本地后端服务** | JSON / MySQL | 本地编辑管理 |
| **Electron 桌面应用** | 内嵌 PyInstaller 后端 | 离线使用，跨平台 |

---

## 🚀 快速开始

### 方式一：在线浏览（无需安装）

直接打开 [**Zoran689.github.io/ZenBlog**](https://Zoran689.github.io/ZenBlog/) 即可阅读全部文章。

### 方式二：下载桌面应用

从 [Releases 页面](https://github.com/Zoran689/ZenBlog/releases/latest) 下载对应平台的安装包，安装后即可使用。

### 方式三：本地运行（开发）

```bash
pip install -r requirements.txt
./start.sh
# 打开 http://localhost:8877
```

### 方式四：Electron 桌面应用（开发）

```bash
npm install
npm start
```

### 打包为桌面应用

```bash
# 1. 先打包 Python 后端
./build_python.sh

# 2. 打包 Electron 应用
npm run pack:mac    # macOS (dmg)
npm run pack:win    # Windows (nsis)
npm run pack:linux  # Linux (AppImage)
```

打包产物输出到 `release/` 目录。

### 停止服务

```bash
./stop.sh
```

---

## 📡 API 接口

所有接口返回 JSON，基础路径 `http://localhost:8877/api`

### 文章

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/article` | 获取文章列表 |
| GET | `/api/article?idx=123` | 获取单篇文章内容 |
| POST | `/api/article` | 创建/保存文章 |
| PUT | `/api/article/rename` | 重命名文章 |
| PUT | `/api/article/move` | 移动到分类 |
| PUT | `/api/article/reorder` | 调整排序 |
| DELETE | `/api/article?idx=123` | 删除文章 |

### 分类

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/categories` | 获取分类列表 |
| POST | `/api/category/add` | 新建分类 |
| PUT | `/api/category/rename` | 重命名分类 |
| PUT | `/api/category/reorder` | 调整分类顺序 |
| DELETE | `/api/category?id=xxx` | 删除分类 |

### 星标

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/stars` | 获取星标列表 |
| POST | `/api/stars` | 保存星标列表 |

---

## 🛠️ 技术细节

- **端口**：`8877`
- **数据存储**：本地 JSON 文件（按每 100 篇一批分文件存储），可选 MySQL
- **CORS**：全开放，支持跨域访问
- **缓存控制**：HTML 响应强制 no-cache，确保前端始终最新
- **CI/CD**：推送 `v*` tag 自动触发 GitHub Actions 构建全平台安装包

## 📝 使用说明

1. **新建文章** → 点击「➕ 新建文章」，填写标题、选择分类、输入 Markdown 内容
2. **编辑文章** → 在文章详情页点击「✏️ 编辑」，修改后「💾 保存」
3. **管理分类** → 侧栏点击「➕」新增，右键重命名或删除
4. **搜索** → 侧栏搜索框输入关键词实时过滤

## 📄 License

MIT
