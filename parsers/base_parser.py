# base_parser.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseJournalParser(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.journal_code = config["journal_code"]

    @abstractmethod
    def parse_html(self, html_content: str) -> List[Dict[str, Any]]:
        """
        抽象方法：解析 HTML 内容，提取期刊文章信息。
        返回一个包含期刊文章信息字典的列表。
        """
        pass