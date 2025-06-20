import json
import re
from datetime import datetime, timedelta, timezone

import requests
from requests.adapters import HTTPAdapter

from module.config.deep import deep_get


class GameRedeemCode:
    def __init__(self, proxy=None):

        self.uid = "80823548"
        self.act_id = None
        self.code_ver = None
        self.deadline = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.proxy = proxy

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

    def get_act_id(self):
        """获取活动ID"""
        url = f"https://bbs-api.mihoyo.com/painter/api/user_instant/list?offset=0&size=20&uid={self.uid}"
        print(url)
        try:
            session = self.new_session()
            response = session.get(url, headers=self.headers)
            data = response.json()

            if data.get("retcode") != 0:
                return False

            for post in deep_get(data, 'data.list', []):
                content = deep_get(post, 'post.post.structured_content', '')
                match = re.search(r'act_id=([^\\]+)', content)
                if match:
                    self.act_id = match.group(1)
                    self._calculate_deadline(deep_get(post, 'post.post.created_at', ''))
                    return True
            return False
        except Exception as e:
            print(f"获取act_id失败: {str(e)}")
            return False

    def _calculate_deadline(self, create_time):
        """计算兑换码过期时间"""
        beijing_tz = timezone(timedelta(hours=8))
        create_time = datetime.fromtimestamp(create_time, tz=beijing_tz)
        self.deadline = (create_time + timedelta(days=1)).replace(hour=23, minute=59, second=59)
        self.expires_iso = self.deadline.isoformat(timespec="seconds")

    def get_live_info(self):
        """获取直播信息"""
        url = "https://api-takumi.mihoyo.com/event/miyolive/index"
        headers = {**self.headers, "x-rpc-act_id": self.act_id}
        print(url)
        print(headers)
        try:
            session = self.new_session()
            response = session.get(url, headers=headers)
            data = response.json()

            if data.get("retcode") != 0:
                return None

            self.code_ver = deep_get(data, 'data.live.code_ver')
            return deep_get(data, 'data.live')
        except Exception as e:
            print(f"获取直播信息失败: {str(e)}")
            return None

    def get_redeem_codes(self):
        """获取兑换码列表"""
        if not self.get_act_id():
            return None

        live_info = self.get_live_info()
        if not live_info or live_info["remain"] > 0:
            return None

        url = (f"https://api-takumi-static.mihoyo.com/event/miyolive/refreshCode?version={self.code_ver}&time="
               f"{int(datetime.now().timestamp())}")
        headers = {**self.headers, "x-rpc-act_id": self.act_id}
        print(url)
        print(headers)
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            code_list = deep_get(data, 'data.code_list', [])
            return [code["code"] for code in code_list]
        except Exception as e:
            print(f"获取兑换码失败: {str(e)}")
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

    def save_to_file(self, filename="codes_cn.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.generate_output(), f, indent=2, ensure_ascii=False)


# 使用示例
if __name__ == "__main__":
    # 支持的游戏类型：原神、星铁/崩铁、崩坏三/崩坏3、绝区零
    redeem_code_fetcher = GameRedeemCode()  # 修改此处切换游戏

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
