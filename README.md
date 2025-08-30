# 🧪 Journal-Scout: 学术期刊爬虫和浏览器

[![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.x-black?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com/)
[![Playwright](https://img.shields.io/badge/Playwright-1.2x-green?style=for-the-badge&logo=playwright)](https://playwright.dev/)

这是一个基于Flask和Playwright的Web应用程序，用于抓取、存储和搜索学术期刊文章。它具有基于Web的UI，用于管理抓取任务、查看结果和高级搜索。

## ✨ 主要功能

*   **📰 多期刊支持**：通过中心化配置轻松扩展以支持新期刊。
*   **⚙️ 批量抓取**：按卷和期号定义抓取任务。
*   **🛡️ 动态代理**：与Clash API集成，可自动切换代理节点以避免被阻止。
*   **🤖 Cloudflare处理**：自动处理Cloudflare质询，并为手动交互提供有头浏览器后备。
*   **🖥️ Web UI**：用于启动抓取、监控进度和搜索文章的用户友好界面。
*   **🔍 高级搜索**：按日期范围、关键字、作者和期刊代码筛选文章。
*   **🗄️ SQLite数据库**：用于存储抓取数据的轻量级、自包含的数据库。

## 🛠️ 技术栈

*   **后端**：Flask
*   **抓取**：Playwright, Requests
*   **解析**：Beautiful Soup
*   **数据库**：SQLite
*   **前端**：HTML, CSS, JavaScript

## 🚀 安装

1.  克隆存储库：
    ```bash
    git clone https://github.com/jackhu5/journal-scout.git
    cd journal-scout
    ```

2.  创建并激活Conda环境：
    ```bash
    conda create -n journal-scout python=3.11
    conda activate journal-scout
    ```

3.  安装Python依赖项：
    ```bash
    pip install -r requirements.txt
    ```

4.  安装Playwright浏览器（仅Chromium）：
    ```bash
    playwright install chromium
    ```

## ▶️ 用法

1.  **启动应用程序**：
    ```bash
    python app.py
    ```
    Web服务器将在 `http://127.0.0.1:5000` 上启动。

2.  **配置代理**（可选）：
    *   在[`config.py`](config.py:97)中编辑`PROXY_SETTINGS`用于静态代理。
    *   在[`config.py`](config.py:106)中编辑`CLASH_API_CONFIG`用于与Clash API动态集成。

3.  **使用Web界面**：
    *   打开浏览器并导航到 `http://127.0.0.1:5000`。
    *   使用“抓取”部分启动单个URL或批量抓取。
    *   使用“搜索”部分按各种条件筛选和查找文章。
    *   在主页上查看数据库统计信息。

## 📂 项目结构
```
├── app.py                  # Flask应用主入口
├── config.py               # 核心配置 (期刊, 代理, UA)
├── requirements.txt        # Python依赖
├── crawlers/               # 爬虫模块
│   ├── base_crawler.py     # 爬虫基类
│   └── acs_crawler.py      # ACS期刊专用爬虫 (使用Playwright)
├── parsers/                # HTML解析模块
│   ├── base_parser.py      # 解析器基类
│   └── acs_parser.py       # ACS期刊专用解析器 (使用BeautifulSoup)
├── databases/              # 数据库文件
│   └── journals.db         # SQLite数据库
├── templates/              # Flask HTML模板
└── utils/                  # 工具模块
    └── clash_manager.py    # Clash API交互工具
