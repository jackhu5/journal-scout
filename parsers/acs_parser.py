# acs_parser.py
from bs4 import BeautifulSoup
from typing import List, Dict, Any

from .base_parser import BaseJournalParser

class AcsJournalParser(BaseJournalParser):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

    def parse_html(self, html_content: str) -> List[Dict[str, Any]]:
        """
        解析 HTML 内容，提取期刊文章信息。
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        articles_data = []

        articles = soup.find_all('div', class_='issue-item')

        for article in articles:
            title_tag = article.find('h3', class_='issue-item_title')
            if not title_tag:
                continue
            
            title_link = title_tag.find('a')
            if not title_link:
                continue

            title = title_link.text.strip()
            article_url = self.config["base_url"] + title_link['href'] # 使用配置中的 base_url
            doi = title_link['href'].replace("/doi/", "")

            date_tag = article.find('span', class_='pub-date-value')
            date = date_tag.text.strip() if date_tag else "No date found"

            authors_list = []
            authors_container = article.find('ul', class_='issue-item_loa')
            if authors_container:
                for author_span in authors_container.find_all('span', class_='hlFld-ContribAuthor'):
                    authors_list.append(author_span.text.strip())
            authors = ', '.join(authors_list) if authors_list else "No authors found"

            abstract_content = article.find('div', class_='accordion__content toc-item__abstract')
            abstract = abstract_content.find('span', class_='hlFld-Abstract').text.strip() if abstract_content and abstract_content.find('span', class_='hlFld-Abstract') else "No abstract found"

            articles_data.append({
                "title": title,
                "url": article_url,
                "doi": doi,
                "date": date,
                "authors": authors,
                "abstract": abstract,
                "journal_code": self.journal_code # 添加期刊代码
            })
        return articles_data