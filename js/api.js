/**
 * ZenBlog API 适配层
 * 
 * 支持两种模式：
 * 1. 后端模式（默认）：通过 fetch 调用 FastAPI 后端
 * 2. 纯静态模式（GitHub Pages）：使用 localStorage 存储所有数据
 * 
 * 自动检测：如果后端不可用（fetch 失败），自动降级为纯静态模式
 */

const ZenAPI = (() => {
    // ── 模式 ──────────────────────────────────────────────
    let _mode = 'auto'; // 'auto' | 'backend' | 'static'
    let _backendReady = false;

    // ── localStorage 键名 ─────────────────────────────────
    const LS_INDEX = 'zenblog_index';
    const LS_CONTENT_PREFIX = 'zenblog_content_';
    const LS_STARS = 'zenblog_stars';

    // ── 初始化 ────────────────────────────────────────────
    async function init() {
        // 尝试检测后端
        try {
            const resp = await fetch('/api/stars', { method: 'GET', signal: AbortSignal.timeout(1000) });
            if (resp.ok) {
                _mode = 'backend';
                _backendReady = true;
                console.log('[ZenAPI] 后端模式');
                return;
            }
        } catch(e) {}
        // 降级为纯静态模式
        _mode = 'static';
        console.log('[ZenAPI] 纯静态模式 (localStorage)');
    }

    function isBackend() { return _mode === 'backend'; }
    function isStatic() { return _mode !== 'backend'; }

    // ── localStorage 辅助 ─────────────────────────────────
    function _lsGet(key, def = null) {
        try {
            const v = localStorage.getItem(key);
            return v ? JSON.parse(v) : def;
        } catch(e) { return def; }
    }

    function _lsSet(key, data) {
        localStorage.setItem(key, JSON.stringify(data));
    }

    function _lsRemove(key) {
        localStorage.removeItem(key);
    }

    // ── 索引操作 ──────────────────────────────────────────
    function _getIndex() {
        const data = _lsGet(LS_INDEX, { articles: [], categories: {}, stars: [] });
        // 兼容：如果 categories 是数组格式，转为对象格式
        if (Array.isArray(data.categories)) {
            const obj = {};
            for (const c of data.categories) {
                obj[c.name] = { icon: c.icon || '📄', order: c.order !== undefined ? c.order : 999 };
            }
            data.categories = obj;
        }
        return data;
    }

    function _saveIndex(data) {
        _lsSet(LS_INDEX, data);
    }

    // ── 内容操作 ──────────────────────────────────────────
    function _getBatchKey(idx) {
        const batchIdx = Math.floor(idx / 100);
        return LS_CONTENT_PREFIX + batchIdx;
    }

    function _getContent(idx) {
        const batch = _lsGet(_getBatchKey(idx), {});
        return batch[String(idx)] || null;
    }

    function _saveContent(idx, content) {
        const key = _getBatchKey(idx);
        const batch = _lsGet(key, {});
        batch[String(idx)] = content;
        _lsSet(key, batch);
    }

    function _deleteContent(idx) {
        const key = _getBatchKey(idx);
        const batch = _lsGet(key, {});
        delete batch[String(idx)];
        _lsSet(key, batch);
    }

    function _getNextId() {
        const idx = _getIndex();
        const articles = idx.articles || [];
        if (articles.length === 0) return 1;
        return Math.max(...articles.map(a => a.idx)) + 1;
    }

    function _now() {
        return new Date().toISOString().replace('T', ' ').substring(0, 19);
    }

    // ── 公开 API ──────────────────────────────────────────

    /**
     * 获取文章列表（含分类/星标元数据）
     * 静态模式下，如果 localStorage 为空，自动从 data/index.json 加载初始数据
     */
    async function getArticles() {
        if (_mode === 'backend') {
            try {
                const resp = await fetch('/api/article');
                if (resp.ok) return await resp.json();
            } catch(e) {}
        }
        // 静态模式：检查 localStorage 是否有数据
        let data = _getIndex();
        const articles = data.articles || [];
        if (articles.length === 0) {
            // 尝试从静态文件加载初始数据
            try {
                const resp = await fetch('data/index.json');
                if (resp.ok) {
                    const fileData = await resp.json();
                    // 合并文件数据到 localStorage
                    const merged = {
                        articles: fileData.articles || [],
                        categories: fileData.categories || {},
                        stars: fileData.stars || [],
                        cat_orders: fileData.cat_orders || {},
                        stock_lessons: fileData.stock_lessons || {}
                    };
                    _lsSet(LS_INDEX, merged);
                    data = _getIndex(); // 重新获取（经过格式转换）
                }
            } catch(e) {
                console.warn('[ZenAPI] 无法从 data/index.json 加载初始数据:', e);
            }
        }
        return data;
    }

    /**
     * 获取单篇文章内容
     */
    async function getArticle(idx) {
        if (_mode === 'backend') {
            try {
                const resp = await fetch(`/api/article?idx=${idx}`);
                if (resp.ok) return await resp.json();
            } catch(e) {}
        }
        const index = _getIndex();
        const meta = (index.articles || []).find(a => a.idx === idx) || null;
        const content = _getContent(idx);
        return { idx, content: content || '', meta };
    }

    /**
     * 保存文章（新建或更新）
     */
    async function saveArticle({ idx, content, title, category }) {
        if (_mode === 'backend') {
            try {
                const resp = await fetch('/api/article', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ idx, content, title, category })
                });
                if (resp.ok) return await resp.json();
            } catch(e) {}
        }
        // 静态模式
        if (idx == null) idx = _getNextId();
        _saveContent(idx, content || '');

        const index = _getIndex();
        const existing = (index.articles || []).find(a => a.idx === idx);
        if (existing) {
            if (title) existing.title = title;
            if (category) existing.category = category;
            existing.updated = _now();
        } else {
            index.articles = index.articles || [];
            index.articles.push({
                idx,
                title: title || `未命名文章 ${idx}`,
                category: category || 'default',
                created: _now(),
                updated: _now()
            });
        }
        _saveIndex(index);
        return { status: 'saved', idx };
    }

    /**
     * 重命名文章
     */
    async function renameArticle(idx, title) {
        if (_mode === 'backend') {
            try {
                const resp = await fetch('/api/article/rename', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ idx, title })
                });
                if (resp.ok) return await resp.json();
            } catch(e) {}
        }
        const index = _getIndex();
        const article = (index.articles || []).find(a => a.idx === idx);
        if (article) article.title = title;
        _saveIndex(index);
        return { status: 'ok' };
    }

    /**
     * 移动文章到分类
     */
    async function moveArticle(idx, category) {
        if (_mode === 'backend') {
            try {
                const resp = await fetch('/api/article/move', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ idx, category })
                });
                if (resp.ok) return await resp.json();
            } catch(e) {}
        }
        const index = _getIndex();
        const article = (index.articles || []).find(a => a.idx === idx);
        if (article) article.category = category;
        _saveIndex(index);
        return { status: 'ok' };
    }

    /**
     * 删除文章
     */
    async function deleteArticle(idx) {
        if (_mode === 'backend') {
            try {
                const resp = await fetch(`/api/article?idx=${idx}`, { method: 'DELETE' });
                if (resp.ok) return await resp.json();
            } catch(e) {}
        }
        const index = _getIndex();
        index.articles = (index.articles || []).filter(a => a.idx !== idx);
        _saveIndex(index);
        _deleteContent(idx);
        return { status: 'deleted' };
    }

    /**
     * 重排文章顺序
     */
    async function reorderArticles(articles) {
        if (_mode === 'backend') {
            try {
                const resp = await fetch('/api/article/reorder', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ articles })
                });
                if (resp.ok) return await resp.json();
            } catch(e) {}
        }
        const index = _getIndex();
        const orderMap = {};
        for (const o of articles) orderMap[o.idx] = o.order;
        for (const a of index.articles || []) {
            if (orderMap[a.idx] !== undefined) a.order = orderMap[a.idx];
        }
        _saveIndex(index);
        return { status: 'ok' };
    }

    /**
     * 获取分类列表
     */
    async function getCategories() {
        if (_mode === 'backend') {
            try {
                const resp = await fetch('/api/categories');
                if (resp.ok) return await resp.json();
            } catch(e) {}
        }
        return _getIndex();
    }

    /**
     * 新增分类
     */
    async function addCategory(name) {
        if (_mode === 'backend') {
            try {
                const resp = await fetch('/api/category/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name })
                });
                if (resp.ok) return await resp.json();
            } catch(e) {}
        }
        const index = _getIndex();
        index.categories = index.categories || {};
        const order = Object.keys(index.categories).length;
        index.categories[name] = { icon: '📄', order };
        _saveIndex(index);
        return { id: name, name, order };
    }

    /**
     * 重命名分类
     */
    async function renameCategory(oldName, newName) {
        if (_mode === 'backend') {
            try {
                const resp = await fetch('/api/category/rename', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ old_name: oldName, new_name: newName })
                });
                if (resp.ok) return await resp.json();
            } catch(e) {}
        }
        const index = _getIndex();
        if (index.categories[oldName]) {
            index.categories[newName] = index.categories[oldName];
            delete index.categories[oldName];
        }
        _saveIndex(index);
        return { status: 'ok' };
    }

    /**
     * 重排分类顺序
     */
    async function reorderCategories(catNames) {
        if (_mode === 'backend') {
            try {
                const resp = await fetch('/api/category/reorder', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ order: catNames })
                });
                if (resp.ok) return await resp.json();
            } catch(e) {}
        }
        const index = _getIndex();
        for (let i = 0; i < catNames.length; i++) {
            const name = catNames[i];
            if (index.categories[name]) {
                index.categories[name].order = i;
            }
        }
        _saveIndex(index);
        return { status: 'ok' };
    }

    /**
     * 删除分类
     */
    async function deleteCategory(name, moveTo = 'default') {
        if (_mode === 'backend') {
            try {
                const resp = await fetch(`/api/category?name=${encodeURIComponent(name)}&move_to=${encodeURIComponent(moveTo)}`, { method: 'DELETE' });
                if (resp.ok) return await resp.json();
            } catch(e) {}
        }
        const index = _getIndex();
        delete index.categories[name];
        for (const a of index.articles || []) {
            if (a.category === id) a.category = moveTo;
        }
        _saveIndex(index);
        return { status: 'deleted' };
    }

    /**
     * 获取星标
     */
    async function getStars() {
        if (_mode === 'backend') {
            try {
                const resp = await fetch('/api/stars');
                if (resp.ok) {
                    const data = await resp.json();
                    return data.starred_idxs || data || [];
                }
            } catch(e) {}
        }
        return _lsGet(LS_STARS, []);
    }

    /**
     * 保存星标
     */
    async function saveStars(stars) {
        if (_mode === 'backend') {
            try {
                const resp = await fetch('/api/stars', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(stars)
                });
                if (resp.ok) return await resp.json();
            } catch(e) {}
        }
        _lsSet(LS_STARS, stars);
        return { status: 'ok' };
    }

    /**
     * 加载文章内容（支持静态文件 + localStorage 回退）
     */
    async function loadContent(idx) {
        // 先检查 localStorage 缓存
        const cached = _getContent(idx);
        if (cached) return cached;

        // 尝试从静态文件加载
        const batchIdx = Math.floor(idx / 100);
        try {
            const resp = await fetch(`data/content_${batchIdx}.json`);
            if (resp.ok) {
                const data = await resp.json();
                // 缓存到 localStorage
                const key = _getBatchKey(idx);
                const batch = _lsGet(key, {});
                for (const [k, v] of Object.entries(data)) {
                    batch[k] = v;
                }
                _lsSet(key, batch);
                return data[String(idx)] || null;
            }
        } catch(e) {}
        return null;
    }

    /**
     * 保存文章内容到 localStorage
     */
    async function saveContent(idx, content) {
        _saveContent(idx, content);
        return { status: 'saved' };
    }

    return {
        init,
        isBackend,
        isStatic,
        getArticles,
        getArticle,
        saveArticle,
        renameArticle,
        moveArticle,
        deleteArticle,
        reorderArticles,
        getCategories,
        addCategory,
        renameCategory,
        reorderCategories,
        deleteCategory,
        getStars,
        saveStars,
        loadContent,
        saveContent
    };
})();
