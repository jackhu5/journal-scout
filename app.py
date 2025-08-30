from flask import Flask, request, jsonify, render_template, Response
import sqlite3
import json
import os
import sys
from pathlib import Path
import importlib
import traceback
import threading
import uuid
import time

# 导入配置
from config import JOURNAL_CONFIGS, MAX_REQUEST_TIMEOUT, MAX_PLAYWRIGHT_WAIT_MS, CLASH_API_CONFIG, CLASH_EXCLUDE_KEYWORDS
from crawlers.base_crawler import BaseJournalCrawler
from parsers.base_parser import BaseJournalParser
from utils.clash_manager import ClashManager

app = Flask(__name__)
DATABASE = 'databases/journals.db'
COOKIE_DIR = 'cookies'
# 确保cookie目录存在
os.makedirs(COOKIE_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DATABASE), exist_ok=True)

# 用于存储批量任务状态的全局字典
batch_tasks = {}
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # c.execute("DROP TABLE IF EXISTS journals")  # 移除每次启动时清空数据库的操作
    c.execute('''
        CREATE TABLE IF NOT EXISTS journals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        journal_code TEXT NOT NULL,
        title TEXT NOT NULL,
        url TEXT NOT NULL UNIQUE,
        doi TEXT,
        date TEXT,
        authors TEXT,
        abstract TEXT,
        date_iso TEXT
        )
    ''')
    # Add date_iso column if it doesn't exist for backward compatibility
    try:
        c.execute("ALTER TABLE journals ADD COLUMN date_iso TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass # Column already exists

    # Backfill date_iso for existing rows
    c.execute("SELECT id, date FROM journals WHERE date_iso IS NULL")
    rows_to_update = c.fetchall()
    if rows_to_update:
        print(f"Backfilling date_iso for {len(rows_to_update)} rows...")
        from datetime import datetime
        for row_id, date_str in rows_to_update:
            if date_str:
                try:
                    # This is where the conversion happens
                    date_iso = datetime.strptime(date_str, '%B %d, %Y').strftime('%Y-%m-%d')
                    c.execute("UPDATE journals SET date_iso = ? WHERE id = ?", (date_iso, row_id))
                except (ValueError, TypeError):
                    pass # Skip rows with invalid date format
        conn.commit()
        print("Backfilling complete.")

    conn.close()

@app.route('/')
def index():
    return render_template('index.html', journal_configs=JOURNAL_CONFIGS)

@app.route('/batch_crawl_page')
def batch_crawl_page():
    return render_template('batch_crawl.html')

# @app.route('/get_cookie_page')
# def get_cookie_page():
#     return render_template('get_cookie.html')

@app.route('/crawl', methods=['POST'])
def crawl():
    data = request.json
    target_url = data.get('url')
    journal_code = data.get('journal_code')

    if not target_url:
        return jsonify({"status": "error", "message": "URL is required"}), 400
    if not journal_code:
        return jsonify({"status": "error", "message": "Journal code is required"}), 400

    config = JOURNAL_CONFIGS.get(journal_code)
    if not config:
        return jsonify({"status": "error", "message": f"Unknown journal code: {journal_code}"}), 400

    try:
        # 动态导入爬虫类
        crawler_module = importlib.import_module("crawlers.acs_crawler")
        CrawlerClass = getattr(crawler_module, config["crawler_class"])
        crawler_instance: BaseJournalCrawler = CrawlerClass(config)
        print(f"爬虫类: {CrawlerClass}")  # 添加日志
        
        html_content, cookies, error = crawler_instance.crawl_page(target_url, cookie_dir=COOKIE_DIR, headless=False) # 允许自动切换到非无头模式
        print(f"从 {target_url} 获取到的 HTML 内容长度: {len(html_content) if html_content else 0}")  # 添加日志
        
        if error:
            if "Cloudflare challenge resolution timed out" in str(error):
                return jsonify({"status": "error", "message": f"Cloudflare 挑战未解决，请在弹出的浏览器窗口中手动完成验证。URL: {target_url}"}), 500
            else:
                return jsonify({"status": "error", "message": f"爬取 {target_url} 失败: {error}"}), 500
        
        if not html_content:
            return jsonify({"status": "error", "message": f"未从 {target_url} 获取到 HTML 内容"}), 500
        
        # 动态导入解析器类
        parser_module = importlib.import_module(config['parser_module'])
        ParserClass = getattr(parser_module, "AcsJournalParser")  # 直接使用正确的类名
        parser_instance: BaseJournalParser = ParserClass(config)
        
        journal_articles = parser_instance.parse_html(html_content)
        
        # 存储到数据库
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        inserted_count = 0
        updated_count = 0
        for article in journal_articles:
            from datetime import datetime
            date_iso = None
            try:
                date_iso = datetime.strptime(article['date'], '%B %d, %Y').strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                pass

            # 使用 INSERT OR REPLACE 实现 UPSERT 功能
            c.execute(
                "INSERT OR REPLACE INTO journals (journal_code, title, url, doi, date, authors, abstract, date_iso) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (article['journal_code'], article['title'], article['url'], article['doi'], article['date'], article['authors'], article['abstract'], date_iso)
            )
            
            # 检查是否是新插入还是更新
            if c.lastrowid:
                inserted_count += 1
                print(f"新增文章: {article['title'][:50]}...")
            else:
                updated_count += 1
                print(f"更新文章: {article['title'][:50]}...")
        conn.commit()
        conn.close()
        
        print(f"成功爬取并保存了 {inserted_count} 篇新文章，更新了 {updated_count} 篇文章")  # 添加日志
        return jsonify({"status": "success", "message": f"Successfully crawled and saved {inserted_count} new articles and updated {updated_count} articles from {target_url}"})
    except Exception as e:
        print(f"发生异常: {e}")  # 添加日志
        print(traceback.format_exc())  # 打印完整的 traceback 信息到控制台
        return jsonify({"status": "error", "message": f"服务器内部错误: {e}"}), 500

@app.route('/search_page')
def search_page():
    return render_template('search.html')

@app.route('/journal_configs', methods=['GET'])
def get_journal_configs():
    return jsonify(JOURNAL_CONFIGS)

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    
    query = "SELECT j.journal_code, j.title, j.url, j.doi, j.date, j.authors, j.abstract, c.name as journal_name FROM journals j "
    
    # Dynamically generate a subquery for journal names to join
    journal_names_subquery_parts = []
    for code, config in JOURNAL_CONFIGS.items():
        journal_names_subquery_parts.append(f"SELECT '{code}' as journal_code, '{config['name']}' as name")
    
    if journal_names_subquery_parts:
        journal_names_subquery = " UNION ALL ".join(journal_names_subquery_parts)
        query += f"LEFT JOIN ( {journal_names_subquery} ) c ON j.journal_code = c.journal_code"

    conditions = []
    params = []

    # Date range
    if data.get('date_from'):
        conditions.append("j.date_iso >= ?")
        params.append(data['date_from'])
    if data.get('date_to'):
        conditions.append("j.date_iso <= ?")
        params.append(data['date_to'])

    # Keywords
    for field in ['title', 'author', 'abstract']:
        keywords = data.get(f'{field}_keywords')
        search_type = data.get(f'{field}_search_type', 'fuzzy')
        if keywords:
            field_conditions = []
            for keyword in keywords:
                if search_type == 'exact':
                    field_conditions.append(f"j.{'authors' if field == 'author' else field} = ?")
                    params.append(keyword)
                else: # fuzzy
                    field_conditions.append(f"j.{'authors' if field == 'author' else field} LIKE ?")
                    params.append(f"%{keyword}%")
            conditions.append(f"({' OR '.join(field_conditions)})")

    # Journal codes
    if data.get('journal_codes'):
        placeholders = ','.join('?' for _ in data['journal_codes'])
        conditions.append(f"j.journal_code IN ({placeholders})")
        params.extend(data['journal_codes'])

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY j.date_iso DESC, j.title ASC"

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute(query, params)
    
    filtered_journals = c.fetchall()
    conn.close()

    journal_list = []
    for journal in filtered_journals:
        journal_list.append({
            "journal_code": journal[0],
            "title": journal[1],
            "url": journal[2],
            "doi": journal[3],
            "date": journal[4],
            "authors": journal[5],
            "abstract": journal[6],
            "journal_name": journal[7]
        })

    return jsonify(journal_list)


@app.route('/journals', methods=['GET'])
def get_journals():
    journal_code = request.args.get('journal_code')
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    if journal_code:
        c.execute("SELECT journal_code, title, url, doi, date, authors, abstract FROM journals WHERE journal_code = ? ORDER BY date DESC, title ASC", (journal_code,))
    else:
        c.execute("SELECT journal_code, title, url, doi, date, authors, abstract FROM journals ORDER BY date DESC, title ASC")
    journals = c.fetchall()
    conn.close()

    journal_list = []
    for journal in journals:
        journal_list.append({
            "journal_code": journal[0],
            "title": journal[1],
            "url": journal[2],
            "doi": journal[3],
            "date": journal[4],
            "authors": journal[5],
            "abstract": journal[6]
        })
    return jsonify(journal_list)

@app.route('/journal_stats', methods=['GET'])
def get_journal_stats():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT journal_code, COUNT(*) FROM journals GROUP BY journal_code")
    journal_counts = c.fetchall()
    conn.close()

    stats = []
    for journal_code, count in journal_counts:
        journal_name = JOURNAL_CONFIGS.get(journal_code, {}).get('name', 'Unknown')
        stats.append({"journal_code": journal_code, "journal_name": journal_name, "count": count})
    return jsonify(stats)

@app.route('/clear_db', methods=['POST'])
def clear_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DELETE FROM journals")
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Database cleared successfully."})

def validate_batch_params(data):
    """验证批量爬取参数"""
    try:
        volume_start = int(data.get('volume_start', 0))
        volume_end = int(data.get('volume_end', 0))
        issue_start = int(data.get('issue_start', 0))
        issue_end = int(data.get('issue_end', 0))
        
        if any(x < 0 for x in [volume_start, volume_end, issue_start, issue_end]):
            return {"valid": False, "message": "输入值不能为负数"}
        
        if volume_start > volume_end:
            return {"valid": False, "message": "Volume起始值不能大于结束值"}
        
        if issue_start > issue_end:
            return {"valid": False, "message": "Issue起始值不能大于结束值"}
        
        return {"valid": True, "params": {
            "journal_code": data['journal_code'],
            "volume_start": volume_start,
            "volume_end": volume_end,
            "issue_start": issue_start,
            "issue_end": issue_end
        }}
        
    except (ValueError, TypeError):
        return {"valid": False, "message": "请输入有效的数字"}

def generate_batch_urls(params):
    """根据参数生成批量爬取的URL列表"""
    journal_code = params['journal_code']
    config = JOURNAL_CONFIGS.get(journal_code)
    if not config:
        raise ValueError(f"未知的期刊代码: {journal_code}")
    
    urls = []
    for volume in range(params['volume_start'], params['volume_end'] + 1):
        for issue in range(params['issue_start'], params['issue_end'] + 1):
            url = f"{config['base_url']}/toc/{journal_code}/{volume}/{issue}"
            urls.append(url)
    return urls

def run_crawl_task(task_id, urls, journal_code):
    """在后台线程中运行的爬取任务"""
    task = batch_tasks[task_id]
    
    config = JOURNAL_CONFIGS.get(journal_code)
    
    clash_manager = None
    try:
        if CLASH_API_CONFIG and CLASH_API_CONFIG.get("api_base_url"):
            clash_manager = ClashManager(
                api_base_url=CLASH_API_CONFIG["api_base_url"],
                secret=CLASH_API_CONFIG.get("secret")
            )
    except (ValueError, ConnectionError) as e:
        print(f"Failed to initialize Clash Manager: {e}. Proxy switching will be disabled.")
        task['errors'].append({"url": "Clash Manager 初始化失败", "error": str(e)})

    try:
        crawler_module = importlib.import_module("crawlers.acs_crawler")
        CrawlerClass = getattr(crawler_module, config["crawler_class"])
        crawler_instance: BaseJournalCrawler = CrawlerClass(config)

        parser_module = importlib.import_module(config['parser_module'])
        ParserClass = getattr(parser_module, "AcsJournalParser")
        parser_instance: BaseJournalParser = ParserClass(config)

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        for url in urls:
            if task['status'] == 'stopped':
                break
            
            # Switch proxy before crawling each URL
            if clash_manager:
                try:
                    new_node = clash_manager.switch_to_random_proxy(
                        CLASH_API_CONFIG["proxy_group"],
                        exclude_keywords=CLASH_EXCLUDE_KEYWORDS
                    )
                    if new_node:
                        task['current_proxy_node'] = new_node
                    else:
                        task['errors'].append({"url": url, "error": "Failed to switch to a new proxy node."})
                except Exception as e:
                    print(f"Error switching proxy node: {e}")
                    task['errors'].append({"url": url, "error": f"Error switching proxy node: {e}"})

            task['current_url'] = url
            
            try:
                # 传入 headless=False 允许爬虫在无头模式失败时自动切换到交互模式
                html_content, _, error = crawler_instance.crawl_page(url, cookie_dir=COOKIE_DIR, headless=False)
                
                if error:
                    # 如果 crawl_page 内部的重试逻辑都失败了，才抛出异常
                    raise Exception(str(error))

                if not html_content:
                    raise Exception("未获取到HTML内容")

                journal_articles = parser_instance.parse_html(html_content)

                for article in journal_articles:
                    from datetime import datetime
                    date_iso = None
                    try:
                        date_iso = datetime.strptime(article['date'], '%B %d, %Y').strftime('%Y-%m-%d')
                    except (ValueError, TypeError):
                        pass
                    c.execute(
                        "INSERT OR REPLACE INTO journals (journal_code, title, url, doi, date, authors, abstract, date_iso) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (article['journal_code'], article['title'], article['url'], article['doi'], article['date'], article['authors'], article['abstract'], date_iso)
                    )
                
                conn.commit()
                task['successful'] += 1
            
            except Exception as e:
                task['failed'] += 1
                task['errors'].append({"url": url, "error": str(e)})
            
            finally:
                task['processed'] += 1
                task['progress_percentage'] = round((task['processed'] / task['total_urls']) * 100, 1)
        
        conn.close()

    except Exception as e:
        task['status'] = 'failed'
        task['errors'].append({"url": "任务初始化失败", "error": str(e)})
        return

    if task['status'] != 'stopped':
        task['status'] = 'completed'

@app.route('/batch_crawl', methods=['POST'])
def batch_crawl():
    data = request.json
    
    validation = validate_batch_params(data)
    if not validation['valid']:
        return jsonify({"status": "error", "message": validation['message']}), 400
    
    urls = generate_batch_urls(validation['params'])
    if not urls:
        return jsonify({"status": "error", "message": "根据所给范围未生成任何URL。"}), 400

    task_id = str(uuid.uuid4())
    batch_tasks[task_id] = {
        "status": "running",
        "total_urls": len(urls),
        "processed": 0,
        "successful": 0,
        "failed": 0,
        "current_url": "",
        "current_proxy_node": "N/A",
        "progress_percentage": 0,
        "start_time": time.time(),
        "errors": []
    }

    thread = threading.Thread(target=run_crawl_task, args=(task_id, urls, data['journal_code']))
    thread.start()

    return jsonify({"status": "success", "task_id": task_id, "total_urls": len(urls)})

@app.route('/batch_progress/<task_id>')
def batch_progress(task_id):
    def generate():
        task = batch_tasks.get(task_id)
        if not task:
            yield f"data: {json.dumps({'status': 'not_found'})}\n\n"
            return
        
        while task['status'] in ['running', 'stopped']:
            yield f"data: {json.dumps(task)}\n\n"
            time.sleep(1)
            if task['status'] == 'stopped':
                break
        
        # Send final status
        yield f"data: {json.dumps(task)}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/batch_stop/<task_id>', methods=['POST'])
def batch_stop(task_id):
    task = batch_tasks.get(task_id)
    if task:
        task['status'] = 'stopped'
        return jsonify({"status": "success", "message": "任务已标记为停止。"})
    return jsonify({"status": "error", "message": "未找到任务。"}), 404

# @app.route('/get_cookie', methods=['POST'])
# def get_cookie():
#     data = request.json
#     journal_code = data.get('journal_code')
#
#     if not journal_code:
#         return jsonify({"status": "error", "message": "Journal code is required"}), 400
#
#     config = JOURNAL_CONFIGS.get(journal_code)
#     if not config:
#         return jsonify({"status": "error", "message": f"Unknown journal code: {journal_code}"}), 400
#
#     try:
#         crawler_module = importlib.import_module("crawlers.acs_crawler")
#         CrawlerClass = getattr(crawler_module, config["crawler_class"])
#         crawler_instance: BaseJournalCrawler = CrawlerClass(config)
#
#         # 构建目标URL，通常是期刊的主页
#         target_url = config.get("base_url")
#
#         # 这个新方法需要在 AcsJournalCrawler 中实现
#         cookies, error = crawler_instance.get_cookies_interactively(target_url, cookie_dir=COOKIE_DIR)
#
#         if error:
#             return jsonify({"status": "error", "message": f"获取Cookie失败: {error}"}), 500
#
#         if not cookies:
#             return jsonify({"status": "error", "message": "未能获取到任何Cookie。"}), 500
#
#         # 检查是否获得了关键的cf_clearance cookie
#         cf_found = any(c['name'] == 'cf_clearance' for c in cookies)
#
#         return jsonify({
#             "status": "success",
#             "message": "Cookie获取成功。",
#             "cookie_count": len(cookies),
#             "cf_found": cf_found
#         })
#
#     except Exception as e:
#         print(traceback.format_exc())
#         return jsonify({"status": "error", "message": f"服务器内部错误: {e}"}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, threaded=True)