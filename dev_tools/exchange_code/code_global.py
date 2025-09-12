import json
import re
from datetime import datetime, timedelta, timezone

import requests
from requests.adapters import HTTPAdapter

from module.config.deep import deep_get


class GameRedeemCode:
    def __init__(self, proxy=None):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.proxy = proxy
        self.post_id = None
        self.expires_iso = None

    def new_session(self):
        session = requests.Session()
        session.trust_env = False
        if self.proxy:
            proxies = {'http': self.proxy, 'https': self.proxy}
            session.proxies = proxies
        session.mount('http://', HTTPAdapter(max_retries=3))
        session.mount('https://', HTTPAdapter(max_retries=3))
        session.headers.update(self.headers)
        session.headers['Content-Type'] = 'application/json'
        session.headers['Accept'] = 'application/json'
        return session

    def get_post_id(self):
        """获取活动帖子ID"""
        url = "https://bbs-api-os.hoyolab.com/community/post/wapi/getNewsList?gids=6&page_size=15&type=3"
        try:
            session = self.new_session()
            response = session.get(url)
            response.raise_for_status()  # 添加HTTP状态码检查
            data = response.json()

            if data.get("retcode") != 0:
                print("API返回错误状态码")
                return False

            for post in deep_get(data, 'data.list', []):
                content = deep_get(post, 'post.multi_language_info.lang_subject.zh-cn', '')
                if "前瞻" in content:
                    self.post_id = deep_get(post, 'post.post_id')
                    return True
            return False
        except requests.exceptions.RequestException as e:
            print(f"网络请求失败: {str(e)}")
            return False
        except Exception as e:
            print(f"解析数据异常: {str(e)}")
            return False

    def get_redeem_codes(self):
        """获取兑换码核心逻辑"""
        if not self.get_post_id():
            return None

        url = f"https://bbs-api-os.hoyolab.com/community/post/wapi/getPostFull?post_id={self.post_id}"
        try:
            session = self.new_session()
            response = session.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            # 提取内容部分
            content = deep_get(data, 'data.post.post.structured_content')
            create_at = deep_get(data, 'data.post.post.created_at')

            # 时间处理
            beijing_tz = timezone(timedelta(hours=8))
            create_time = datetime.fromtimestamp(create_at, tz=beijing_tz)
            self.deadline = (create_time + timedelta(days=1)).replace(
                hour=23, minute=59, second=59, microsecond=0
            )
            self.expires_iso = self.deadline.isoformat(timespec="seconds")

            # 使用更精确的正则表达式
            code_pattern = r'(?<=code=)[A-Z0-9]{8,16}(?=\\?")'
            return re.findall(code_pattern, content)

        except requests.exceptions.RequestException as e:
            print(f"获取帖子内容失败: {str(e)}")
            return None
        except Exception as e:
            print(f"处理数据异常: {str(e)}")
            return None

    def generate_output(self):
        """生成结构化输出"""
        codes = self.get_redeem_codes()
        if not codes:
            return {
                "error": {
                    "code": 404,
                    "message": "当前没有可用的兑换码",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }

        return {
            "data": {
                "codes": [
                    {
                        "code": code,
                        "expires_at": self.expires_iso,
                    } for code in codes
                ]
            }
        }

    def save_to_file(self, filename="codes_global.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.generate_output(), f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # 初始化兑换码获取器
    redeem_code_fetcher = GameRedeemCode()

    # 获取并输出结果
    result = redeem_code_fetcher.generate_output()
    redeem_code_fetcher.save_to_file()

    # 配置JSON输出格式
    print(json.dumps(
        result,
        indent=2,
        ensure_ascii=False,  # 支持中文显示
        default=str,  # 处理可能的datetime对象
        sort_keys=False  # 保持字段顺序
    ))
