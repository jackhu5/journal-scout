# acs_crawler.py
import requests
import re
import json
import time
import random
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import traceback
import threading
from typing import List, Dict, Any, Tuple, Optional

from .base_crawler import BaseJournalCrawler
from config import MAX_REQUEST_TIMEOUT, MAX_PLAYWRIGHT_WAIT_MS, PROXY_SETTINGS

# --- Helper Function: is_cf_challenge ---
def is_cf_challenge(html_content: str | None) -> bool:
    """
    更精确地检测是否为 Cloudflare 挑战页面。
    """
    if not html_content:
        return False
    return (
        "Just a moment" in html_content and
        (
            "<title>Just a moment" in html_content or
            "Checking your browser" in html_content or
            ("cdn-cgi/challenge-platform" in html_content and "__cf_chl_opt" in html_content)
        )
    )

# --- Helper Function: Convert requests.Cookies to Playwright format ---
def requests_cookies_to_playwright_list(requests_cookies: requests.cookies.RequestsCookieJar) -> List[Dict]:
    """
    将 requests.CookiesJar 对象转换为 Playwright 的 add_cookies 方法期望的列表格式。
    """
    cookie_list: List[Dict] = []
    for cookie in requests_cookies:
        pw_cookie = {
            "name": cookie.name,
            "value": cookie.value,
            "domain": cookie.domain,
            "path": cookie.path,
            "secure": cookie.secure,
            "httpOnly": cookie.has_nonstandard_attr("HttpOnly"),
            "sameSite": cookie.get("SameSite", "None"),
            "expires": cookie.expires if cookie.expires is not None else -1
        }
        pw_cookie = {k: v for k, v in pw_cookie.items() if v is not None}
        cookie_list.append(pw_cookie)
    return cookie_list

class AcsJournalCrawler(BaseJournalCrawler):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # self.user_agent is now set in the BaseJournalCrawler parent class
        self.max_request_timeout = config.get("max_request_timeout", MAX_REQUEST_TIMEOUT)
        self.max_playwright_wait_ms = config.get("max_playwright_wait_ms", MAX_PLAYWRIGHT_WAIT_MS)

    def _fetch_page_with_playwright(
        self,
        url: str,
        initial_cookies: List[Dict] | None = None,
        headless: bool = True
    ) -> Tuple[Optional[str], Optional[List[Dict]], Optional[Exception]]:
        browser = None
        context = None
        page = None
        final_html = None
        final_cookies = None
        error_obj = None

        print(f"Playwright: Attempting to access {url} with headless={headless}")

        try:
            with sync_playwright() as p:
                print(f"Playwright: Launching browser (headless={headless})...")
                launch_options = {
                    "headless": headless,
                    "args": [
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        f"--user-agent={self.user_agent}",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-extensions",
                        "--disable-gpu",
                    ]
                }
                
                # Apply proxy settings if configured
                if PROXY_SETTINGS and PROXY_SETTINGS.get("server"):
                    print(f"Playwright: Using proxy server {PROXY_SETTINGS['server']}")
                    launch_options["proxy"] = PROXY_SETTINGS
                
                browser = p.chromium.launch(**launch_options)
                
                context = browser.new_context(
                            user_agent=self.user_agent,
                            locale="en-US",
                            timezone_id="America/Los_Angeles",
                            java_script_enabled=True,
                        )
                
                if initial_cookies:
                    print(f"Playwright: Loading {len(initial_cookies)} cookies into context.")
                    context.add_cookies(initial_cookies)

                page = context.new_page()
                
                # 在页面加载前注入脚本，隐藏自动化工具特征
                page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                print(f"Playwright: Navigating to {url}...")
                
                # 增加随机延迟，模拟人类操作
                time.sleep(random.uniform(1, 3))
                
                page.goto(url, wait_until="domcontentloaded", timeout=self.max_playwright_wait_ms)
                print("Playwright: Initial navigation complete. Checking for challenge...")

                start_time = time.time()
                solved = False

                while (time.time() - start_time) * 1000 < self.max_playwright_wait_ms:
                    # Wait for network to be idle or specific selector to appear before getting content
                    try:
                        page.wait_for_load_state('networkidle', timeout=5000) # Wait up to 5 seconds for network idle
                    except PlaywrightTimeoutError:
                        pass # Continue if network is not idle, page might still be usable

                    current_html = page.content()
                    current_title = page.title()
                    cf_clearance_cookie = next ( (c for c in context.cookies() if c["name"] == "cf_clearance"), None)

                    if not is_cf_challenge(current_html) and "Just a moment" not in current_title and cf_clearance_cookie:
                        print("Playwright: Cloudflare challenge solved successfully!")
                        final_html = current_html
                        final_cookies = context.cookies()
                        solved = True
                        break

                    if (time.time() - start_time) * 1000 >= self.max_playwright_wait_ms:
                        break

                    page.wait_for_timeout(300)

                if not solved:
                    raise PlaywrightTimeoutError(f"Cloudflare challenge resolution timed out after {self.max_playwright_wait_ms}ms.")
                
        except PlaywrightTimeoutError as e:
            print(f"Playwright Timeout Error: {e}")
            error_obj = e
        except Exception as e:
            print(f"Playwright General Error: {e}")
            traceback.print_exc()
            error_obj = e
        
        return final_html, final_cookies, error_obj

    def crawl_page(self, url: str, cookie_dir: str = 'cookies', headless: bool = True) -> Tuple[Optional[str], Optional[List[Dict]], Optional[Exception]]:
        # saved_cookies = self._load_cookies(cookie_dir=cookie_dir) # 注释掉加载cookie的步骤
        saved_cookies = [] # 确保始终以无cookie状态启动
        
        # 1. 直接使用 Playwright 无头模式尝试
        print(f"\nAttempting to crawl {url} with Playwright (headless)...")
        playwright_html, playwright_cookies, playwright_error = self._fetch_page_with_playwright(
            url, saved_cookies, headless=True
        )

        if playwright_html:
            print("Playwright successfully fetched the page content in headless mode.")
            self._save_cookies(playwright_cookies, cookie_dir=cookie_dir)
            return playwright_html, playwright_cookies, None

        # 2. 如果无头模式失败，则切换到有头模式重试
        print(f"Playwright failed in headless mode. Error: {playwright_error}")
        print("Retrying with non-headless Playwright for manual interaction...")
        
        playwright_html_interactive, playwright_cookies_interactive, playwright_error_interactive = self._fetch_page_with_playwright(
            url, saved_cookies, headless=False,
        )

        if playwright_html_interactive:
            print("Playwright successfully fetched the page content in interactive (non-headless) mode.")
            self._save_cookies(playwright_cookies_interactive, cookie_dir=cookie_dir)
            return playwright_html_interactive, playwright_cookies_interactive, None
        
        # 3. 如果两种模式都失败，则返回最终的错误
        print(f"Playwright failed in both headless and interactive modes. Final error: {playwright_error_interactive}")
        return None, None, playwright_error_interactive

    def _load_cookies(self, cookie_dir: str = 'cookies') -> List[Dict]:
        cookie_file = Path(cookie_dir) / "cookies.json"
        if cookie_file.exists():
            try:
                with open(cookie_file, "r", encoding="utf-8") as f:
                    cookies: List[Dict] = json.load(f)
                    print(f"Loaded {len(cookies)} cookies from {cookie_file}")
                    return cookies
            except (json.JSONDecodeError, OSError) as e:
                print(f"Error loading cookies from {cookie_file}: {e}")
                return []
        else:
            print(f"Cookie file not found: {cookie_file}")
            return []

    def _save_cookies(self, cookies: List[Dict], cookie_dir: str = 'cookies') -> None:
        """
        用新的cookie完全覆盖现有的cookie文件。
        """
        if not cookies:
            print("No cookies to save.")
            return

        cookie_file = Path(cookie_dir) / "cookies.json"
        
        # 确保目录存在
        Path(cookie_dir).mkdir(parents=True, exist_ok=True)
        
        try:
            with open(cookie_file, "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            print(f"Successfully saved/overwritten {len(cookies)} cookies to {cookie_file}")
        except OSError as e:
            print(f"Error saving cookies to {cookie_file}: {e}")

    def get_cookies_interactively(self, url: str, cookie_dir: str = 'cookies') -> Tuple[Optional[List[Dict]], Optional[Exception]]:
        """
        启动一个交互式浏览器会话，让用户手动操作以获取cookies。
        当用户关闭浏览器后，保存获取到的cookies。
        """
        final_cookies = None
        error_obj = None

        print(f"Playwright: Launching interactive browser to get cookies for {url}")

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=False,  # 必须是交互模式
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        f"--user-agent={self.user_agent}",
                        "--disable-blink-features=AutomationControlled",
                    ]
                )
                
                context = browser.new_context(
                    user_agent=self.user_agent,
                    locale="en-US",
                    timezone_id="America/Los_Angeles",
                    java_script_enabled=True,
                )
                
                page = context.new_page()
                page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

                print(f"Playwright: Navigating to {url}. Please complete any human verification.")
                page.goto(url, wait_until="domcontentloaded", timeout=self.max_playwright_wait_ms * 2) # 交互模式给更长的超时

                print("Playwright: Page loaded. Waiting for you to manually close the browser...")

                # 使用 page.on('close') 来检测页面/浏览器是否关闭
                closed_event = threading.Event()
                def handle_close(page):
                    print("Browser page closed by user.")
                    closed_event.set()
                
                page.on('close', handle_close)
                
                # 等待关闭事件被触发
                closed_event.wait()

                final_cookies = context.cookies()
                self._save_cookies(final_cookies, cookie_dir=cookie_dir)
                
        except Exception as e:
            print(f"Playwright interactive session error: {e}")
            traceback.print_exc()
            error_obj = e
        
        return final_cookies, error_obj