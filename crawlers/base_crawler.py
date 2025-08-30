# base_crawler.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
import json
import random
from pathlib import Path
from config import USER_AGENT_LIST

class BaseJournalCrawler(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.journal_code = config["journal_code"]
        self.cookie_file = config["cookie_file"]
        # If a specific user_agent is provided in the config, use it. Otherwise, pick a random one from the list.
        self.user_agent = config.get("user_agent", random.choice(USER_AGENT_LIST))
        self.max_request_timeout = config.get("max_request_timeout", 15)
        self.max_playwright_wait_ms = config.get("max_playwright_wait_ms", 60000)
        
        # Ensure data directory for cookies exists
        Path(self.cookie_file).parent.mkdir(parents=True, exist_ok=True)

    def _load_cookies(self) -> Optional[List[Dict]]:
        cookie_file_path = Path(self.cookie_file)
        if cookie_file_path.exists():
            try:
                with open(cookie_file_path, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                    print(f"Loaded {len(cookies)} cookies from {self.cookie_file}")
                    return cookies
            except (json.JSONDecodeError, OSError) as e:
                print(f"Error loading cookies from {cookie_file}: {e}. Fetching fresh.")
        return None

    def _save_cookies(self, cookies: List[Dict], cookie_dir: str = 'cookies'):
        if cookies:
            cookie_file =  Path(cookie_dir) / "cookies.json"
            Path(cookie_dir).mkdir(parents=True, exist_ok=True)
            with open(cookie_file, "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(cookies)} cookies to {cookie_file}")

    @abstractmethod
    def crawl_page(self, url: str, cookie_dir: str = 'cookies', headless: bool = True) -> Tuple[Optional[str], Optional[List[Dict]], Optional[Exception]]:
        """
        抽象方法：爬取指定 URL 的页面内容和 cookies。
        返回 (html_content, cookies, error_obj)
        """
        pass
        
    @abstractmethod
    def get_cookies_interactively(self, url: str, cookie_dir: str = 'cookies') -> Tuple[Optional[List[Dict]], Optional[Exception]]:
        """
        抽象方法：通过交互式浏览器会话获取并保存 cookies。
        返回 (cookies, error_obj)
        """
        pass