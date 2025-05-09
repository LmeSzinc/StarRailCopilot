import requests
import re
from datetime import datetime, timedelta


class GameRedeemCode:
    def __init__(self, game_type="原神"):
        # 游戏类型映射
        self.game_map = {
            "原神": "75276539",
            "星铁": "80823548",
            "崩铁": "80823548",
            "崩坏三": "73565430",
            "崩坏3": "73565430",
            "绝区零": "152039148"
        }

        self.uid = self.game_map.get(game_type, "75276539")
        self.act_id = None
        self.code_ver = None
        self.deadline = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def get_act_id(self):
        """获取活动ID"""
        url = f"https://bbs-api.mihoyo.com/painter/api/user_instant/list?offset=0&size=20&uid={self.uid}"
        print(url)
        try:
            response = requests.get(url, headers=self.headers)
            data = response.json()

            if data.get("retcode") != 0:
                return False

            for post in data["data"]["list"]:
                content = post.get("post", {}).get("post", {}).get("structured_content", "")
                match = re.search(r'act_id=([^\\]+)', content)
                if match:
                    self.act_id = match.group(1)
                    self._calculate_deadline(post["post"]["post"]["created_at"])
                    return True
            return False
        except Exception as e:
            print(f"获取act_id失败: {str(e)}")
            return False

    def _calculate_deadline(self, create_time):
        """计算兑换码过期时间"""
        create_date = datetime.fromtimestamp(create_time)

        if self.uid in ["80823548", "152039148"]:  # 星铁/绝区零
            self.deadline = (create_date + timedelta(days=1)).replace(hour=23, minute=59, second=59)
        elif self.uid == "73565430":  # 崩坏三
            self.deadline = (create_date + timedelta(days=5)).replace(hour=12, minute=0, second=0)
        else:  # 原神
            self.deadline = (create_date + timedelta(days=5)).replace(hour=12, minute=0, second=0)

    def get_live_info(self):
        """获取直播信息"""
        url = "https://api-takumi.mihoyo.com/event/miyolive/index"
        headers = {**self.headers, "x-rpc-act_id": self.act_id}
        print(url)
        print(headers)
        try:
            response = requests.get(url, headers=headers)
            data = response.json()

            if data.get("retcode") != 0:
                return None

            self.code_ver = data["data"]["live"]["code_ver"]
            return data["data"]["live"]
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

        url = f"https://api-takumi-static.mihoyo.com/event/miyolive/refreshCode?version={self.code_ver}&time={int(datetime.now().timestamp())}"
        headers = {**self.headers, "x-rpc-act_id": self.act_id}
        print(url)
        print(headers)
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            return [code["code"] for code in data["data"]["code_list"]]
        except Exception as e:
            print(f"获取兑换码失败: {str(e)}")
            return None

    def format_result(self):
        """格式化输出结果"""
        codes = self.get_redeem_codes()
        if not codes:
            return "当前没有可用的兑换码"

        return (
                f"🕒 过期时间: {self.deadline.strftime('%Y-%m-%d %H:%M:%S')}\n"
                "🎮 兑换码列表：\n" +
                "\n".join([f"▸ {code}" for code in codes])
        )


# 使用示例
if __name__ == "__main__":
    # 支持的游戏类型：原神、星铁/崩铁、崩坏三/崩坏3、绝区零
    game = GameRedeemCode(game_type="星铁")  # 修改此处切换游戏

    result = game.format_result()
    print(result)
