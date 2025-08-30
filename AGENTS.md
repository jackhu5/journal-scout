# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## 项目特定的非显而易见信息

### 运行命令
- 启动应用: `python app.py` (Flask开发服务器，默认端口5000)
- 测试: `pytest` (需要先安装依赖)
- 代码格式化: `black .` 和 `isort .`
- 类型检查: `mypy .`
- 安全检查: `bandit -r .` 和 `safety check`

### 关键架构约定
- **爬虫自动降级机制**: [`crawl_page()`](crawlers/acs_crawler.py:160) 先尝试无头模式，失败后自动切换到有头模式供用户手动处理Cloudflare
- **Cookie管理**: 每次爬取都从空Cookie开始 ([`saved_cookies = []`](crawlers/acs_crawler.py:162))，不加载已保存的Cookie
- **数据库UPSERT**: 使用 `INSERT OR REPLACE` 而非标准INSERT，基于URL唯一性约束
- **日期双格式存储**: 同时存储原始日期字符串和ISO格式 (`date_iso`) 用于排序和查询

### 配置依赖
- **期刊配置**: 所有期刊必须在 [`JOURNAL_CONFIGS`](config.py:3) 中定义，包含 `crawler_class` 和 `parser_module`
- **代理设置**: [`PROXY_SETTINGS`](config.py:97) 和 [`CLASH_API_CONFIG`](config.py:106) 控制网络代理行为
- **Clash节点过滤**: [`CLASH_EXCLUDE_KEYWORDS`](config.py:114) 排除特定关键词的代理节点

### 爬虫特殊行为
- **Cloudflare检测**: [`is_cf_challenge()`](crawlers/acs_crawler.py:17) 检测多种CF挑战模式
- **User-Agent轮换**: 从 [`USER_AGENT_LIST`](config.py:34) 随机选择，模拟真实浏览器
- **批量任务状态**: 使用全局字典 [`batch_tasks`](app.py:27) 跟踪后台爬取进度

### 解析器约定
- **URL构建**: 解析器必须使用 `config["base_url"]` 拼接相对链接
- **必需字段**: 每个文章必须包含 `journal_code` 字段用于数据库存储
- **日期格式**: 期望 "Month DD, YYYY" 格式，会自动转换为ISO格式

### 数据库模式
- **向后兼容**: 启动时自动添加 `date_iso` 列并回填现有数据
- **唯一约束**: URL字段有UNIQUE约束，支持UPSERT操作
- **搜索优化**: 使用动态JOIN查询期刊名称而非存储冗余数据