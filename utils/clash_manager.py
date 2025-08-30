import requests
import random
from typing import List, Dict, Optional, Any

class ClashManager:
    """
    一个用于通过 RESTful API 与 Clash 核心交互的管理器。
    """
    def __init__(self, api_base_url: str, secret: Optional[str] = None):
        """
        初始化 ClashManager。

        :param api_base_url: Clash External Controller (API) 的地址, e.g., "http://127.0.0.1:9090"
        :param secret: 如果 API 设置了密码，请提供。
        """
        if not api_base_url:
            raise ValueError("Clash API base URL cannot be empty.")
        self.api_base_url = api_base_url
        self.headers = {"Content-Type": "application/json"}
        if secret:
            self.headers["Authorization"] = f"Bearer {secret}"
        
        # Test connection on init
        self.get_version()

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """通用请求方法"""
        url = f"{self.api_base_url}{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, timeout=5, **kwargs)
            response.raise_for_status()
            # PUT/PATCH requests might not return a body on success (e.g., 204 No Content)
            if response.status_code == 204 or not response.content:
                return None
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to Clash API at {url}. Ensure Clash is running and the API is enabled. Error: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to decode JSON from Clash API response. URL: {url}. Error: {e}. Response text: {response.text}")

    def get_version(self) -> Dict[str, str]:
        """获取Clash核心的版本信息，用于测试连接。"""
        print(f"Connecting to Clash API at {self.api_base_url}...")
        version_info = self._make_request("GET", "/version")
        print(f"Successfully connected to Clash! Version: {version_info.get('version')}")
        return version_info

    def get_proxies(self) -> Dict[str, Any]:
        """获取所有的代理和代理组信息。"""
        return self._make_request("GET", "/proxies")

    def get_proxy_group_nodes(self, group_name: str, exclude_keywords: Optional[List[str]] = None) -> Optional[List[str]]:
        """
        获取指定代理组下的所有可用节点名称。

        :param group_name: 代理组的名称 (e.g., "PROXY", "UrlTest")
        :param exclude_keywords: 一个包含要排除的关键词的列表。
        :return: 节点名称列表，如果找不到该组则返回 None。
        """
        all_proxies = self.get_proxies()
        group = all_proxies.get("proxies", {}).get(group_name)
        if not (group and group.get("all")):
            return None

        all_nodes = group["all"]
        
        # 基础过滤，排除掉策略组和默认的非代理节点
        filtered_nodes = [
            p for p in all_nodes
            if all_proxies.get("proxies", {}).get(p, {}).get("type") != "Selector"
        ]

        # 关键词过滤
        if exclude_keywords:
            final_nodes = []
            for node in filtered_nodes:
                if not any(keyword in node for keyword in exclude_keywords):
                    final_nodes.append(node)
            return final_nodes
        
        return filtered_nodes

    def switch_proxy(self, group_name: str, proxy_name: str) -> bool:
        """
        切换指定代理组到指定的节点。

        :param group_name: 要切换的代理组名称。
        :param proxy_name: 目标节点的名称。
        :return: 切换成功返回 True, 否则返回 False。
        """
        endpoint = f"/proxies/{group_name}"
        payload = {"name": proxy_name}
        try:
            self._make_request("PUT", endpoint, json=payload)
            print(f"Successfully switched proxy group '{group_name}' to '{proxy_name}'.")
            return True
        except ConnectionError as e:
            print(f"Error switching proxy: {e}")
            return False

    def switch_to_random_proxy(self, group_name: str, exclude_keywords: Optional[List[str]] = None) -> Optional[str]:
        """
        随机切换指定代理组的一个节点。

        :param group_name: 代理组名称。
        :param exclude_keywords: 要排除的节点关键词列表。
        :return: 切换到的新节点名称，如果失败则返回 None。
        """
        nodes = self.get_proxy_group_nodes(group_name, exclude_keywords=exclude_keywords)
        if not nodes:
            print(f"Could not find any valid nodes in group '{group_name}'.")
            return None
        
        new_node = random.choice(nodes)
        if self.switch_proxy(group_name, new_node):
            return new_node
        return None

if __name__ == '__main__':
    # --- 使用示例 ---
    # 该脚本现在会从 config.py 导入配置来进行测试
    try:
        # To make this script runnable from the project root, we need to adjust the sys.path
        import sys
        import os
        # Add the project root to the Python path
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from config import CLASH_API_CONFIG, CLASH_EXCLUDE_KEYWORDS
    except ImportError:
        print("Error: Could not import CLASH_API_CONFIG from config.py.")
        print("Please ensure config.py exists in the project root and is correctly configured.")
        exit(1)

    if not CLASH_API_CONFIG or not CLASH_API_CONFIG.get("api_base_url"):
        print("Error: CLASH_API_CONFIG is not defined or is missing 'api_base_url' in config.py.")
        exit(1)

    CLASH_API_URL = CLASH_API_CONFIG["api_base_url"]
    CLASH_API_SECRET = CLASH_API_CONFIG.get("secret")
    PROXY_GROUP_TO_SWITCH = CLASH_API_CONFIG.get("proxy_group", "PROXY")
    EXCLUDE_KEYWORDS = CLASH_EXCLUDE_KEYWORDS or []

    print("--- Clash Manager Test Script ---")
    try:
        # 初始化 Manager
        manager = ClashManager(api_base_url=CLASH_API_URL, secret=CLASH_API_SECRET)
        
        # 获取并打印指定组下的所有节点
        print(f"\nFetching nodes for proxy group: '{PROXY_GROUP_TO_SWITCH}'...")
        nodes = manager.get_proxy_group_nodes(PROXY_GROUP_TO_SWITCH, exclude_keywords=EXCLUDE_KEYWORDS)
        
        if nodes:
            print(f"\nSuccessfully found {len(nodes)} nodes:")
            # For better readability, print one node per line
            for i, node in enumerate(nodes):
                print(f"  {i+1:2d}. {node}")
        else:
            print(f"\nCould not find any valid nodes in group '{PROXY_GROUP_TO_SWITCH}'.")
            print("Please check the 'proxy_group' name in your config.py and your Clash configuration.")

    except (ValueError, ConnectionError) as e:
        print(f"\nAn error occurred: {e}")