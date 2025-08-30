# config.py

JOURNAL_CONFIGS = {
    "jmcmar": {
        "name": "Journal of Medicinal Chemistry",
        "base_url": "https://pubs.acs.org",
        "toc_path_template": "/toc/jmcmar/0/0",
        "cookie_file": "cookies/cookies.json",
        "parser_module": "parsers.acs_parser",
        "crawler_class": "AcsJournalCrawler",
        "journal_code": "jmcmar"
    },
    "jacsat": {
        "name": "Journal of the American Chemical Society",
        "base_url": "https://pubs.acs.org",
        "toc_path_template": "/toc/jacsat/0/0",
        "cookie_file": "cookies/cookies.json",
        "parser_module": "parsers.acs_parser",
        "crawler_class": "AcsJournalCrawler",
        "journal_code": "jacsat"
    },
    # 可以添加其他期刊的配置
    # "another_journal": {
    #     "name": "Another Journal",
    #     "base_url": "https://another.pub.com",
    #     "toc_path_template": "/toc/{journal_code}/current",
    #     "cookie_file": "data/cookies_another.json",
    #     "parser_module": "another_parser",
    #     "crawler_class": "AnotherJournalCrawler",
    #     "journal_code": "another_journal"
    # }
}

USER_AGENT_LIST = [
    # Windows 10/11, Chrome 126
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.2572.65',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.57 Safari/537.36',
    
    # Windows 10/11, Chrome 125
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.142 Safari/537.36',

    # Windows 10/11, Chrome 124
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.208 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.61 Safari/537.36',
    
    # Windows 10/11, Chrome 123
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.122 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.59 Safari/537.36',
    
    # Windows 10/11, Chrome 122
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.129 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.95 Safari/537.36',

    # Windows 10/11, Chrome 121
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.185 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.86 Safari/537.36',

    # Windows 10/11, Chrome 120
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.225 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.71 Safari/537.36',

    # Windows 10/11, Chrome 119
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.200 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.160 Safari/537.36',
    
    # Windows 10/11, Chrome 118
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.118 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.71 Safari/537.36',

    # Windows 10/11, Chrome 117
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.150 Safari/537.36',
]
MAX_REQUEST_TIMEOUT = 15
MAX_PLAYWRIGHT_WAIT_MS = 60000

# --- 代理设置 ---
# 如果您需要使用代理，请在此处填写您的代理服务器信息。
# 如果 PROXY_SETTINGS 为 None 或 server 为空，则不使用代理。
# 示例:
# PROXY_SETTINGS = {
#     "server": "http://127.0.0.1:7890",  # 支持 http, https, socks5
#     # "username": "your_username",     # 如果需要认证，请取消注释并填写
#     # "password": "your_password"      # 如果需要认证，请取消注释并填写
# }
PROXY_SETTINGS = {
     "server": "http://127.0.0.1:1080",  # 支持 http, https, socks5
     # "username": "your_username",     # 如果需要认证，请取消注释并填写
     # "password": "your_password"      # 如果需要认证，请取消注释并填写
 }

# --- Clash API 设置 ---
# 用于通过 API 自动切换节点
# 如果 CLASH_API_CONFIG 为 None 或 api_base_url 为空，则不启用此功能。
CLASH_API_CONFIG = {
    "api_base_url": "http://127.0.0.1:38184", # 您的 Clash external-controller 地址
    "secret": "43d681b0-6844-443a-8747-707b6c24616b",                         # 如果设置了 secret key，请填写
    "proxy_group": "GLOBAL"                  # 您想要自动切换的代理组的名称
}

# --- Clash 节点过滤 ---
# 在随机选择节点时，排除掉节点名称中包含以下任何关键词的节点
CLASH_EXCLUDE_KEYWORDS = [
    "流量", "重置", "到期", "官网", "订阅",
    "自动选择", "故障转移", "负载均衡",
    "DIRECT", "REJECT", "台湾3"
]